import json
import os
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import Body, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .ai_schemas import AIChatRequest, AIChatResponse
from .auth import create_access_token
from .database import SessionLocal, engine
from .deps import get_current_user, get_db

app = FastAPI()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@app.on_event("startup")
def on_startup():
    # Auto-migrate: if the users table exists with the old schema (username column),
    # drop all tables so create_all rebuilds them with the new schema.
    inspector = sa_inspect(engine)
    if inspector.has_table("users"):
        old_cols = {c["name"] for c in inspector.get_columns("users")}
        if "username" in old_cols or "email" not in old_cols:
            models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        crud.seed_default_data(session)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/hello")
def api_hello():
    return {"message": "Backend is working"}


# ---------------------------------------------------------------------------
# Auth — Google OAuth 2.0
# ---------------------------------------------------------------------------

@app.get("/api/auth/google")
def google_login():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")
    state = secrets.token_urlsafe(32)
    params = {
        "client_id": client_id,
        "redirect_uri": f"{base_url}/api/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
    }
    redirect = RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}")
    redirect.set_cookie("oauth_state", state, max_age=300, httponly=True, samesite="lax")
    return redirect


@app.get("/api/auth/google/callback")
def google_callback(
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db),
):
    expected_state = request.cookies.get("oauth_state")
    if not expected_state or state != expected_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8000")

    token_resp = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": f"{base_url}/api/auth/google/callback",
            "grant_type": "authorization_code",
        },
    )
    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange OAuth code")

    access_token = token_resp.json().get("access_token")
    userinfo_resp = httpx.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if userinfo_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch Google user info")

    info = userinfo_resp.json()
    google_id = info.get("sub")
    email = info.get("email")
    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Incomplete user info from Google")

    user = crud.get_user_by_google_id(db, google_id)
    if not user:
        user = crud.create_oauth_user(
            db,
            google_id=google_id,
            email=email,
            display_name=info.get("name"),
            avatar_url=info.get("picture"),
        )
        crud.create_user_default_board(db, user.id)

    token = create_access_token(user.id)
    redirect = RedirectResponse(url="/")
    redirect.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=86400)
    redirect.delete_cookie("oauth_state")
    return redirect


@app.get("/api/auth/me", response_model=schemas.UserOut)
def api_auth_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.post("/api/auth/logout")
def api_auth_logout(response: Response):
    response.delete_cookie("access_token")
    return {"success": True}


@app.post("/api/auth/dev-login", response_model=schemas.UserOut)
def api_dev_login(
    payload: schemas.DevLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """Development-only login bypass. Disabled when APP_ENV=production."""
    if os.getenv("APP_ENV") == "production":
        raise HTTPException(status_code=404)
    user = crud.get_user_by_email(db, payload.email)
    if not user:
        user = crud.create_oauth_user(
            db,
            google_id=f"dev-{payload.email}",
            email=payload.email,
            display_name=payload.email.split("@")[0],
            avatar_url=None,
        )
        crud.create_user_default_board(db, user.id)
    token = create_access_token(user.id)
    response.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=86400)
    return user


# ---------------------------------------------------------------------------
# Board & card endpoints (all require authentication)
# ---------------------------------------------------------------------------

@app.get("/api/boards", response_model=schemas.BoardOut)
def api_get_board(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    board = crud.get_board_for_user(db, current_user.id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return board


@app.post(
    "/api/boards/{board_id}/columns/{column_id}/cards", response_model=schemas.CardOut
)
def api_create_card(
    board_id: int,
    column_id: int,
    payload: schemas.CardCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    column = crud.get_column(db, column_id)
    if not column or column.board_id != board_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return crud.create_card(db, column_id=column_id, title=payload.title, description=payload.description)


@app.patch("/api/cards/{card_id}", response_model=schemas.CardOut)
def api_update_card(
    card_id: int,
    payload: schemas.CardUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = crud.update_card(db, card_id=card_id, title=payload.title, description=payload.description)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card


@app.delete("/api/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_card(
    card_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not crud.delete_card(db, card_id=card_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")


@app.patch("/api/columns/{column_id}", response_model=schemas.ColumnOut)
def api_rename_column(
    column_id: int,
    payload: schemas.ColumnUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    column = crud.rename_column(db, column_id=column_id, title=payload.title)
    if not column:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return column


@app.put("/api/cards/{card_id}/move", response_model=schemas.CardOut)
def api_move_card(
    card_id: int,
    payload: schemas.CardMove,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = crud.move_card(
        db,
        card_id=card_id,
        target_column_id=payload.columnId,
        target_position=payload.position,
    )
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Card or column not found"
        )
    return card


# ---------------------------------------------------------------------------
# AI endpoints
# ---------------------------------------------------------------------------

@app.post("/api/ai/chat", response_model=AIChatResponse)
def api_ai_chat(
    payload: AIChatRequest = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")

    board = crud.get_board_for_user(db, current_user.id)
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    history = crud.get_conversation_history(db, current_user.id)
    crud.append_message(db, current_user.id, "user", payload.question)

    board_json = schemas.BoardOut.model_validate(board).model_dump()
    column_mapping = {col["title"]: col["id"] for col in board_json["columns"]}

    prompt = f"""
You are an AI assistant for a Kanban project management app. The user will ask questions or give instructions about their board.

COLUMN MAPPING (use these IDs when creating cards):
{json.dumps(column_mapping, indent=2)}

Always respond in this exact JSON format:
{{
  "response": "<string, your friendly answer to the user>",
  "boardUpdates": {{
    "cards": [
      {{
        "id": <existing_card_id>,
        "title": "<card_title>",
        "description": "<card_description>",
        "columnId": <column_id_number>,
        "delete": true
      }}
    ],
    "columns": [
      {{
        "id": <existing_column_id>,
        "title": "<new_column_title>"
      }}
    ]
  }}
}}

IMPORTANT RULES:
- For creating NEW cards: include "title", "description", and "columnId" (numeric ID from mapping)
- For updating EXISTING cards: include "id" (numeric). Include "title" and/or "description" if changing them. Include "columnId" if moving to a different column.
- For DELETING cards: include "id" (numeric) and set "delete": true
- For creating NEW columns: include only "title"
- For updating EXISTING columns: include "id" (numeric) and "title"
- If no board changes are needed, set "boardUpdates" to null or omit it entirely
- Always provide a friendly response

Here is the current board JSON:
{json.dumps(board_json)}

Conversation history:
{json.dumps(history)}

User message:
{payload.question}
"""

    try:
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
        )
        ai_content = response.choices[0].message.content
        try:
            parsed = json.loads(ai_content)
            assistant_text = parsed.get("response", ai_content)
            crud.append_message(db, current_user.id, "assistant", assistant_text)
            return AIChatResponse(**parsed)
        except Exception:
            crud.append_message(db, current_user.id, "assistant", ai_content)
            return AIChatResponse(response=ai_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI call failed: {str(e)}")


@app.get("/api/ai/history")
def api_get_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    messages = crud.get_conversation_history(db, current_user.id)
    return {"messages": messages}


@app.delete("/api/ai/history", status_code=status.HTTP_204_NO_CONTENT)
def api_clear_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    crud.clear_conversation_history(db, current_user.id)


@app.get("/api/ai/test")
def api_ai_test():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
    try:
        client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "What is 2+2?"}],
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI call failed: {str(e)}")


# ---------------------------------------------------------------------------
# Static frontend (must be mounted last)
# ---------------------------------------------------------------------------

static_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../frontend/out")
)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

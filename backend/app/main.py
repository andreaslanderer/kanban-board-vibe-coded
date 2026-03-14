import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .ai_schemas import AIChatRequest, AIChatResponse
from .deps import get_db
import json

# In-memory conversation history for MVP (user_id -> list of messages)
conversation_histories = {}

# FastAPI app instance
app = FastAPI()

@app.post("/api/ai/chat", response_model=AIChatResponse)
def api_ai_chat(
    payload: AIChatRequest = Body(...),
    db: Session = Depends(get_db),
):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OpenRouter API key not configured")

    # For MVP, always use the single hardcoded user
    user = crud.get_user_by_username(db, "user")
    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User not found")
    board = crud.get_board_for_user(db, user.id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")

    # Conversation history (in-memory, per user)
    history = conversation_histories.setdefault(user.id, [])
    # Add the new user message
    history.append({"role": "user", "content": payload.question})

    # Prepare prompt for AI
    board_json = schemas.BoardOut.model_validate(board).model_dump()
    prompt = f"""
You are an AI assistant for a Kanban project management app. The user will ask questions or give instructions about their board. Always respond in this JSON format:
{{
  \"response\": <string, your answer to the user>,
  \"boardUpdates\": <object, optional, with updated cards/columns if you want to make changes>
}}

Here is the current board JSON:
{json.dumps(board_json)}

Conversation history:
{json.dumps(history)}

User message:
{payload.question}
"""

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        ai_content = response.choices[0].message.content
        # Try to parse as JSON
        try:
            parsed = json.loads(ai_content)
            # Add AI response to history
            history.append({"role": "assistant", "content": parsed.get("response", ai_content)})
            return AIChatResponse(**parsed)
        except Exception:
            # fallback: return raw text
            history.append({"role": "assistant", "content": ai_content})
            return AIChatResponse(response=ai_content)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI call failed: {str(e)}")
from .database import SessionLocal, engine
from .deps import get_db



@app.on_event("startup")
def on_startup():
    # Create database tables and seed default content
    models.Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        crud.seed_default_data(session)


@app.get("/api/hello")
def api_hello():
    return {"message": "Backend is working"}


@app.post("/api/auth/login", response_model=schemas.LoginResponse)
def api_auth_login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, payload.username)
    if not user or user.password_hash != payload.password:
        return schemas.LoginResponse(success=False, message="Invalid username or password")

    return schemas.LoginResponse(success=True, user=user)


@app.get("/api/boards", response_model=schemas.BoardOut)
def api_get_board(db: Session = Depends(get_db)):
    # For MVP we use the single hardcoded user
    user = crud.get_user_by_username(db, "user")
    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User not found")

    board = crud.get_board_for_user(db, user.id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return board


@app.post("/api/boards/{board_id}/columns/{column_id}/cards", response_model=schemas.CardOut)
def api_create_card(board_id: int, column_id: int, payload: schemas.CardCreate, db: Session = Depends(get_db)):
    # validate board/column belong together
    column = crud.get_column(db, column_id)
    if not column or column.board_id != board_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")

    card = crud.create_card(db, column_id=column_id, title=payload.title, description=payload.description)
    return card


@app.patch("/api/cards/{card_id}", response_model=schemas.CardOut)
def api_update_card(card_id: int, payload: schemas.CardUpdate, db: Session = Depends(get_db)):
    card = crud.update_card(db, card_id=card_id, title=payload.title, description=payload.description)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return card


@app.delete("/api/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_card(card_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_card(db, card_id=card_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")


@app.patch("/api/columns/{column_id}", response_model=schemas.ColumnOut)
def api_rename_column(column_id: int, payload: schemas.ColumnUpdate, db: Session = Depends(get_db)):
    column = crud.rename_column(db, column_id=column_id, title=payload.title)
    if not column:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return column


@app.put("/api/cards/{card_id}/move", response_model=schemas.CardOut)
def api_move_card(card_id: int, payload: schemas.CardMove, db: Session = Depends(get_db)):
    card = crud.move_card(db, card_id=card_id, target_column_id=payload.columnId, target_position=payload.position)
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card or column not found")
    return card


@app.get("/api/ai/test")
def api_ai_test():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="OpenRouter API key not configured")

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "What is 2+2?"}]
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI call failed: {str(e)}")


# serve the statically exported frontend at the root (mounted after API routes)
static_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../frontend/out")
)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

@app.get("/api/hello")
def api_hello():
    return {"message": "Backend is working"}

# serve the statically exported frontend at the root (mounted after API routes)
static_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../frontend/out")
)
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

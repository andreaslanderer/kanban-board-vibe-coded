from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def read_root():
    return "<html><body><h1>Hello from backend!</h1></body></html>"


@app.get("/api/hello")
def api_hello():
    return {"message": "Backend is working"}

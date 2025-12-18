
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def index():
    return {"status": "AI Agent Platform Running"}

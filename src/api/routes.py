from fastapi import FastAPI
from pydantic import BaseModel

from src.agent.workflow import analyze_repository
from src.tools.repo_loader import load_repo_files


class AnalyzeRequest(BaseModel):
    repo_url: str


app = FastAPI(title="Agentic GitHub Codebase Intelligence API")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Agentic codebase API is running"}


@app.post("/analyze")
def analyze_repo(request: AnalyzeRequest):
    metadata, files = load_repo_files(request.repo_url)
    report = analyze_repository(metadata, files)
    return report.model_dump()


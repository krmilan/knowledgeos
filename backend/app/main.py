from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="KnowledgeOS API",
    description="AI-powered knowledge management system",
    version="0.1.0"
)

@app.get("/")
def root():
    return {"status": "ok", "message": "KnowledgeOS API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
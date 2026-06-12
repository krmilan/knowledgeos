from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers import auth, workspaces, files

load_dotenv()

app = FastAPI(
    title="KnowledgeOS API",
    description="AI-powered knowledge management system",
    version="0.1.0"
)

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(files.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "KnowledgeOS API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
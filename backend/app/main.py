from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv
from app.routers import auth, workspaces, files, chat
from app.routers.websocket import router as ws_router
from app.routers import graph
from app.websocket_manager import redis_listener
from app.services.vector import ensure_entities_collection
from app.routers import agent

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_entities_collection()
    task = asyncio.create_task(redis_listener())
    yield
    task.cancel()


app = FastAPI(
    title="KnowledgeOS API",
    description="AI-powered knowledge management system",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(files.router)
app.include_router(chat.router)
app.include_router(ws_router)
app.include_router(graph.router)
app.include_router(agent.router, tags=["agent"])

@app.get("/")
def root():
    return {"status": "ok", "message": "KnowledgeOS API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
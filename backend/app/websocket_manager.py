import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket
import redis.asyncio as aioredis
import os

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


class ConnectionManager:
    def __init__(self):
        # workspace_id -> set of active WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, workspace_id: str):
        await websocket.accept()
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = set()
        self.active_connections[workspace_id].add(websocket)

    def disconnect(self, websocket: WebSocket, workspace_id: str):
        if workspace_id in self.active_connections:
            self.active_connections[workspace_id].discard(websocket)
            if not self.active_connections[workspace_id]:
                del self.active_connections[workspace_id]

    async def broadcast_to_workspace(self, workspace_id: str, message: dict):
        """Send message to all connections in a workspace."""
        if workspace_id not in self.active_connections:
            return
        dead = set()
        for websocket in self.active_connections[workspace_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                dead.add(websocket)
        # clean up dead connections
        for ws in dead:
            self.active_connections[workspace_id].discard(ws)


manager = ConnectionManager()


async def publish_to_workspace(workspace_id: str, message: dict):
    """Publish a message via Redis so ALL workers receive it."""
    redis = await aioredis.from_url(REDIS_URL)
    await redis.publish(
        f"workspace:{workspace_id}",
        json.dumps(message)
    )
    await redis.aclose()


async def redis_listener():
    """
    Runs as a background task on startup.
    Subscribes to all workspace channels and broadcasts
    incoming messages to local WebSocket connections.
    """
    redis = await aioredis.from_url(REDIS_URL)
    pubsub = redis.pubsub()
    await pubsub.psubscribe("workspace:*")  # subscribe to ALL workspaces

    async for message in pubsub.listen():
        if message["type"] != "pmessage":
            continue
        try:
            channel = message["channel"].decode()          # "workspace:abc123"
            workspace_id = channel.split(":", 1)[1]
            data = json.loads(message["data"])
            await manager.broadcast_to_workspace(workspace_id, data)
        except Exception:
            continue
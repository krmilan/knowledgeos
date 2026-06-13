from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket_manager import manager, publish_to_workspace

router = APIRouter()


@router.websocket("/ws/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str):
    await manager.connect(websocket, workspace_id)
    try:
        while True:
            # Wait for messages from this client
            data = await websocket.receive_json()

            # Broadcast to everyone in the workspace via Redis
            # so it works even with multiple API workers
            await publish_to_workspace(workspace_id, {
                "type": "message",
                "workspace_id": workspace_id,
                "data": data,
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, workspace_id)
        await publish_to_workspace(workspace_id, {
            "type": "user_left",
            "workspace_id": workspace_id,
        })
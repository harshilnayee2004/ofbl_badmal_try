import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from socket_controller.socket_manager import ConnectionManager

router = APIRouter(
    prefix="/socket/chat",
    tags=["Chat WebSocket"]
)

class ChatConnectionManager(ConnectionManager):
    def __init__(self):
        super().__init__()
        self.role_connections: Dict[str, Set[WebSocket]] = {}

    async def connect_role(self, ws: WebSocket, role: str):
        await ws.accept()
        self.active_connections.add(ws)
        if role not in self.role_connections:
            self.role_connections[role] = set()
        self.role_connections[role].add(ws)

    def disconnect_role(self, ws: WebSocket, role: str):
        self.active_connections.discard(ws)
        if role in self.role_connections:
            self.role_connections[role].discard(ws)
            if not self.role_connections[role]:
                del self.role_connections[role]

    async def broadcast(self, data: dict, exclude_role: str = None):
        for ws in list(self.active_connections):
            # Skip if ws is explicitly assigned to exclude_role 
            if exclude_role and exclude_role in self.role_connections and ws in self.role_connections[exclude_role]:
                continue
            try:
                await ws.send_json(data)
            except Exception:
                # We do a basic discard here
                self.active_connections.discard(ws)

chat_manager = ChatConnectionManager()

@router.websocket("/ws/{role}")
async def websocket_chat_endpoint(websocket: WebSocket, role: str):
    await chat_manager.connect_role(websocket, role)
    try:
        while True:
            data = await websocket.receive_text()
            pass
    except WebSocketDisconnect:
        chat_manager.disconnect_role(websocket, role)

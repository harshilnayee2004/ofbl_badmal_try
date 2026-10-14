from typing import Dict, Set
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Map room_name -> set of WebSockets
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket, room_name: str = None):
        await ws.accept()
        self.active_connections.add(ws)
        if room_name:
            if room_name not in self.rooms:
                self.rooms[room_name] = set()
            self.rooms[room_name].add(ws)

    def disconnect(self, ws: WebSocket, room_name: str = None):
        self.active_connections.discard(ws)
        if room_name and room_name in self.rooms:
            self.rooms[room_name].discard(ws)
            if not self.rooms[room_name]:
                del self.rooms[room_name]
        else:
            # If room_name not provided, remove from all rooms
            for room in list(self.rooms.keys()):
                self.rooms[room].discard(ws)
                if not self.rooms[room]:
                    del self.rooms[room]

    async def broadcast_to_room(self, room_name: str, data: dict):
        if room_name in self.rooms:
            for ws in list(self.rooms[room_name]):
                try:
                    await ws.send_json(data)
                except Exception:
                    self.disconnect(ws, room_name)

    async def send_json(self, data: dict):
        for ws in list(self.active_connections):
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(ws)

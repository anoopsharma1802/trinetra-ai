from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

        if websocket not in self.active_connections:
            self.active_connections.append(websocket)

        print(
            f"[WS] Connected. Active connections: "
            f"{len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        print(
            f"[WS] Disconnected. Active connections: "
            f"{len(self.active_connections)}"
        )

    async def broadcast(self, message: dict):
        print(
            f"[WS] Broadcasting to "
            f"{len(self.active_connections)} connection(s)"
        )

        dead_connections = []

        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
                print("[WS] Message sent successfully")
            except Exception as error:
                print(f"[WS] Send failed: {error}")
                dead_connections.append(connection)

        for connection in dead_connections:
            self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as error:
        print(f"[WS] Connection error: {error}")
        manager.disconnect(websocket)
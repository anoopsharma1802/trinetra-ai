from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, str | None] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()

        self.active_connections[websocket] = None

        print(
            f"[WS] Connected. Active connections: "
            f"{len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)

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

        message_city = message.get("city_name") or message.get("alert", {}).get("city_name")
        for connection, subscribed_city in list(self.active_connections.items()):
            if subscribed_city and message_city and subscribed_city != message_city:
                continue
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
            command = await websocket.receive_text()
            if command.startswith("CITY:"):
                manager.active_connections[websocket] = command.removeprefix("CITY:").strip() or None

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as error:
        print(f"[WS] Connection error: {error}")
        manager.disconnect(websocket)
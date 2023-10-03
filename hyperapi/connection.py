from typing import Any
class WebSocketConnection:
    
    _receive:Any
    _send: Any

    path: str
    query: dict[str, str]
    slugs: dict[str, str]

    async def accept(self):
        await self.send({"type": "websocket.accept"})
    
    async def receive_message(self):
        message = await self.receive()
        if message["type"] == "websocket.receive":
            return message.get("text", "")
        return None

    async def send_message(self, message):
        await self.send({
            "type": "websocket.send",
            "text": message,
        })

    async def close(self, code=1000):
        await self.send({
            "type": "websocket.close",
            "code": code,
        })
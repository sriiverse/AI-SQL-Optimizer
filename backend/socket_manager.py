import logging
from typing import Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps client_id to their active WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_execute_command(self, client_id: str, query: str) -> bool:
        """
        Sends an execution request to the specific client's CLI agent.
        Returns True if the message was sent successfully, False if the client is not connected.
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                # Send the query to the CLI as a JSON string or plain text
                # We'll stick to a simple JSON payload for expandability
                import json
                payload = json.dumps({"type": "EXECUTE", "query": query})
                await websocket.send_text(payload)
                return True
            except Exception as e:
                logger.error(f"Error sending payload to client {client_id}: {e}")
                self.disconnect(client_id)
                return False
        return False

# Global instance to be imported by main.py
manager = ConnectionManager()

"""
Connection manager module.
Handles active WebSocket or DB connections, etc.
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    def connect(self, conn):
        """Register a new connection."""
        self.active_connections.append(conn)

    def disconnect(self, conn):
        """Remove a connection if present."""
        if conn in self.active_connections:
            self.active_connections.remove(conn)

    def broadcast(self, message: str):
        """Send a message to all active connections (stub)."""
        for conn in self.active_connections:
            # Replace with actual send call
            print(f"Broadcasting to {conn}: {message}")

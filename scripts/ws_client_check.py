#!/usr/bin/env python3
import asyncio
import json
import sys
from datetime import datetime

try:
    import websockets  # type: ignore
except ImportError:
    sys.stderr.write(
        "Missing dependency: websockets. Install with: python -m pip install websockets\n"
    )
    sys.exit(2)


async def main() -> int:
    uri = "ws://localhost:8000/ws"
    print(f"[{datetime.now().isoformat()}] Connecting to {uri}")
    try:
        async with websockets.connect(uri) as ws:
            print("✅ WebSocket connected")

            # Receive initial connection message
            try:
                first = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print("📥 First message:", first)
            except asyncio.TimeoutError:
                print("⚠️ No initial message received within 5s")

            # Request an immediate update
            msg = {"type": "request_update"}
            await ws.send(json.dumps(msg))
            print("📤 Sent:", msg)

            # Receive follow-up message
            try:
                second = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print("📥 Second message:", second)
            except asyncio.TimeoutError:
                print("⚠️ No update message received within 5s")

            return 0
    except Exception as e:
        print("❌ WebSocket error:", repr(e))
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

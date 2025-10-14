from starlette.testclient import TestClient

from fba_bench_api.server.app_factory import create_app


def main():
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        # Health
        r1 = client.get("/health", timeout=10)
        print("HEALTH", r1.status_code, r1.text)

        # Settings
        r2 = client.get("/api/v1/settings", timeout=10)
        print("SETTINGS", r2.status_code, r2.text)

        # WebSocket probe (should work in degraded mode without Redis)
        try:
            with client.websocket_connect("/ws/realtime") as ws:
                first = ws.receive_text()
                print("WS first:", first)
                ws.send_text('{"type":"ping"}')
                pong = ws.receive_text()
                print("WS pong:", pong)
        except Exception as e:
            print("WS error:", repr(e))


if __name__ == "__main__":
    main()

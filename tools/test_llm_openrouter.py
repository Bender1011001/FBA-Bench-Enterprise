import json
import urllib.request
import urllib.error

API = "http://127.0.0.1:8000/api/v1/llm/test"

MODELS = [
    "moonshotai/kimi-k2:free",
    "deepseek/deepseek-r1-0528:free",
    "deepseek/deepseek-chat-v3.1:free",
    "x-ai/grok-4-fast:free",
]


def post(model: str) -> str:
    payload = {
        "model": model,
        "temperature": 0.1,
        "max_tokens": 64,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = str(e)
        return f"HTTP {e.code}: {body}"
    except Exception as e:
        return f"ERROR: {e!s}"


def main() -> int:
    print("=== OpenRouter Free Models Connectivity Test ===")
    for m in MODELS:
        print(f"\n--- Testing {m} ---")
        out = post(m)
        print(out)
    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

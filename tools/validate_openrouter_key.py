import json
import os
import sys
import urllib.error
import urllib.request

# Load .env to populate OPENROUTER_API_KEY in local dev
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass


def main() -> int:
    base = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    key = os.getenv("OPENROUTER_API_KEY", "").strip()

    # Sanitize accidental quotes
    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
        key = key[1:-1].strip()

    if not key or not key.startswith("sk-or-v1-"):
        print(json.dumps({"ok": False, "error": "Missing or malformed OPENROUTER_API_KEY"}))
        return 1

    req = urllib.request.Request(
        f"{base}/models",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            # Optional headers; shouldn't be required, but included
            "HTTP-Referer": os.getenv("OPENROUTER_REFERER", "https://fba-bench.local"),
            "X-Title": os.getenv("OPENROUTER_APP_TITLE", "FBA-Bench"),
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print(
                json.dumps(
                    {
                        "ok": True,
                        "status": resp.status,
                        "endpoint": f"{base}/models",
                        "body_preview": body[:400],
                    }
                )
            )
            return 0
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = str(e)
        print(
            json.dumps(
                {"ok": False, "status": e.code, "endpoint": f"{base}/models", "error": body[:400]}
            )
        )
        return 2
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 3


if __name__ == "__main__":
    sys.exit(main())

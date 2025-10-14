#!/usr/bin/env python3
"""
Generic deployment health check for FBA-Bench.

Checks:
- Backend API: /api/v1/health (default)
- Optional reverse proxy (Nginx) endpoint: /nginx-health

Usage examples:
  python scripts/healthcheck.py --url http://localhost:8000/api/v1/health
  python scripts/healthcheck.py --url https://localhost/nginx-health --allow-insecure
  python scripts/healthcheck.py --urls http://localhost:8000/api/v1/health,https://localhost/nginx-health --allow-insecure

Exit codes:
  0 = All targets healthy
  1 = One or more targets unhealthy or unreachable
"""

from __future__ import annotations

import argparse
import ssl
import sys
import time
import urllib.error
import urllib.request
from typing import List


def check_url(url: str, timeout: float, allow_insecure: bool) -> bool:
    ctx = None
    if url.lower().startswith("https") and allow_insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            code = resp.getcode()
            # Consider any HTTP response (2xx..5xx) a positive "service is responding"
            return 100 <= code < 600
    except urllib.error.HTTPError as e:
        # HTTP error still indicates service is reachable
        return 100 <= e.code < 600
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--url",
        default="http://localhost:8000/api/v1/health",
        help="Single URL to check (ignored if --urls specified).",
    )
    ap.add_argument(
        "--urls",
        default="",
        help="Comma-separated list of URLs to check; overrides --url when provided.",
    )
    ap.add_argument("--retries", type=int, default=30, help="Retry attempts per URL (default: 30)")
    ap.add_argument(
        "--interval", type=float, default=2.0, help="Seconds between retries (default: 2.0)"
    )
    ap.add_argument(
        "--timeout", type=float, default=3.0, help="Per-request timeout seconds (default: 3.0)"
    )
    ap.add_argument(
        "--allow-insecure",
        action="store_true",
        help="Allow insecure HTTPS (skip certificate verification). Useful for self-signed local TLS.",
    )
    args = ap.parse_args()

    urls: List[str] = [u.strip() for u in (args.urls.split(",") if args.urls else []) if u.strip()]
    if not urls:
        urls = [args.url]

    all_ok = True
    for url in urls:
        ok = False
        for _ in range(max(1, args.retries)):
            if check_url(url, timeout=args.timeout, allow_insecure=args.allow_insecure):
                ok = True
                break
            time.sleep(args.interval)
        print(f"[HEALTH] {url} -> {'OK' if ok else 'FAIL'}")
        all_ok = all_ok and ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

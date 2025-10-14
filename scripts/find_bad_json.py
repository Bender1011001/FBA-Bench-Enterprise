import json
import pathlib
import sys

root = pathlib.Path("configs")
bad = False

for p in root.rglob("*"):
    if p.suffix.lower() in {".json", ".jsonc"}:  # include .jsonc if someone added comments
        try:
            txt = p.read_text(encoding="utf-8")
            json.loads(txt)  # strict load
        except Exception as e:
            bad = True
            print(f"[BAD] {p} -> {e}")
        else:
            print(f"[OK ] {p}")

if bad:
    sys.exit(1)

"""
Enterprise-to-Core import smoke test.

Prerequisite:
  pip install -r repos/fba-bench-enterprise/requirements.txt

Run:
  python -c "import runpy; runpy.run_path('repos/fba-bench-enterprise/scripts/smoke_core_imports.py')"
"""
def main() -> None:
    failures = []

    def try_import(mod):
        try:
            __import__(mod)
            print(f"[OK] import {mod}")
        except Exception as e:
            print(f"[FAIL] import {mod}: {e}")
            return False
        return True

    # Validate access to core modules after editable install
    targets = [
        "metrics",
        "agents",
        "baseline_bots",
        "constraints",
        "money",
        "fba_bench_core",  # marker package from core
    ]

    for t in targets:
        if not try_import(t):
            failures.append(t)

    if failures:
        raise SystemExit(f"Smoke import failures: {failures}")
    print("Enterprise smoke: all core imports succeeded.")

if __name__ == "__main__":
    main()
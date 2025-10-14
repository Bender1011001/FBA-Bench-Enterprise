import glob
import sys
from pathlib import Path

import yaml


def main() -> int:
    base = Path("configs")
    if not base.exists():
        print(f"configs directory not found at: {base.resolve()}")
        return 2

    patterns = [
        str(base / "**" / "*.yaml"),
        str(base / "**" / "*.yml"),
    ]

    paths = sorted({p for pat in patterns for p in glob.glob(pat, recursive=True)})
    if not paths:
        print(f"No YAML files found under {base.resolve()}")
        return 0

    print(f"Scanning {len(paths)} YAML files under {base.resolve()} ...")
    bad = 0
    lines = []
    for p in paths:
        try:
            with open(p, encoding="utf-8") as f:
                yaml.safe_load(f)
            lines.append(f"OK   {p}")
        except Exception as e:
            bad += 1
            lines.append(f"FAIL {p}: {e}")

    report_path = base / "yaml_validation_report.txt"
    try:
        report_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nReport written to: {report_path.resolve()}")
    except Exception as e:
        print(f"\nCould not write report file: {e}")

    print("\n" + "\n".join(lines))
    if bad:
        print(f"\nSummary: {bad} file(s) failed YAML parsing.")
    else:
        print("\nSummary: All files parsed successfully.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

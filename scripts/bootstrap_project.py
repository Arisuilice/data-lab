#!/usr/bin/env python3
"""Create the minimal data-lab-lite project structure.

Usage:
    python bootstrap_project.py --project-root ./analysis_project --data ./data.csv
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, help="Directory to create or reuse")
    parser.add_argument("--data", action="append", default=[], help="Optional data file to copy into data/raw/")
    parser.add_argument("--force", action="store_true", help="Allow overwriting existing copied data files")
    return parser.parse_args()


def safe_copy(src: Path, dst: Path, *, force: bool = False) -> Path:
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    final = dst / src.name if dst.is_dir() else dst
    if final.exists() and not force:
        stem, suffix = final.stem, final.suffix
        i = 1
        while final.exists():
            final = final.with_name(f"{stem}_{i}{suffix}")
            i += 1
    shutil.copy2(src, final)
    return final


def main() -> None:
    args = parse_args()
    root = Path(args.project_root).resolve()

    for rel in [
        "data/raw",
        "data/processed",
        "scripts",
        "outputs/tables",
        "outputs/figures",
        "outputs/models",
    ]:
        (root / rel).mkdir(parents=True, exist_ok=True)

    copied = []
    for item in args.data:
        copied_path = safe_copy(Path(item).expanduser().resolve(), root / "data/raw", force=args.force)
        copied.append(str(copied_path.relative_to(root)))

    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Data analysis project\n\n"
            "This project uses the minimal data-lab-lite structure.\n\n"
            "- `data/raw/`: original data, do not modify.\n"
            "- `scripts/analyze.py`: main analysis script.\n"
            "- `outputs/report.md`: final report.\n",
            encoding="utf-8",
        )

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "copied_data": copied,
        "structure": [
            "data/raw",
            "data/processed",
            "scripts",
            "outputs/tables",
            "outputs/figures",
            "outputs/models",
        ],
    }
    (root / "outputs" / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

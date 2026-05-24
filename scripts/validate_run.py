#!/usr/bin/env python3
"""Validate a minimal data-lab-lite analysis run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_RUN_SUMMARY_FIELDS = [
    "created_at",
    "goal",
    "task_level",
    "input_files",
    "generated_files",
    "outputs",
    "quality_gates",
    "warnings",
    "next_actions",
]


def artifact_path(item: Any) -> str | None:
    if isinstance(item, str):
        return item
    if isinstance(item, dict) and isinstance(item.get("path"), str):
        return item["path"]
    return None


def resolve_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return project_root / path


def validate_run(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root)
    errors: list[str] = []
    warnings: list[str] = []

    report_path = root / "outputs" / "report.md"
    summary_path = root / "outputs" / "run_summary.json"

    if not report_path.exists():
        errors.append("outputs/report.md is missing")

    if not summary_path.exists():
        errors.append("outputs/run_summary.json is missing")
        return {"ok": False, "errors": errors, "warnings": warnings}

    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"outputs/run_summary.json is invalid JSON: {exc}")
        return {"ok": False, "errors": errors, "warnings": warnings}

    for field in REQUIRED_RUN_SUMMARY_FIELDS:
        if field not in summary:
            errors.append(f"run_summary.json missing required field: {field}")

    generated_files = summary.get("generated_files", [])
    if isinstance(generated_files, list):
        for item in generated_files:
            raw_path = artifact_path(item)
            if raw_path is None:
                errors.append("run_summary.json generated_files contains an item without a path")
                continue
            if not resolve_path(root, raw_path).exists():
                errors.append(f"generated file is missing: {raw_path}")
    else:
        errors.append("run_summary.json generated_files must be a list")

    quality_gates = summary.get("quality_gates")
    if isinstance(quality_gates, dict):
        failed = [name for name, value in quality_gates.items() if value is False]
        if failed:
            warnings.append("quality gates marked false: " + ", ".join(sorted(failed)))
    elif "quality_gates" in summary:
        errors.append("run_summary.json quality_gates must be an object")

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".", help="Analysis project root to validate")
    args = parser.parse_args()

    result = validate_run(args.project_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()

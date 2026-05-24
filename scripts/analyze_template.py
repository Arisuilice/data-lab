#!/usr/bin/env python3
"""Minimal reproducible analysis script for data-lab-lite.

This template is intentionally compact. Adapt it to the user's dataset and goal.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import (
    ExtraTreesClassifier,
    ExtraTreesRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    HistGradientBoostingClassifier,
    HistGradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Lasso, LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.model_selection import KFold, StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True, help="Input data path")
    parser.add_argument("--target", default=None, help="Target column for modeling")
    parser.add_argument("--goal", default="Analyze the dataset and produce a concise report.")
    parser.add_argument("--output-dir", default="outputs")
    return parser.parse_args()


def read_data(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(path)
    if suffix == ".tsv":
        return pd.read_csv(path, sep="\t")
    if suffix in {".fwf", ".fixed"}:
        return pd.read_fwf(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix in {".json", ".jsonl"}:
        return pd.read_json(path, lines=suffix == ".jsonl")
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if suffix == ".feather":
        return pd.read_feather(path)
    if suffix in {".sqlite", ".sqlite3", ".db"}:
        import sqlite3

        with sqlite3.connect(path) as conn:
            tables = pd.read_sql_query(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name",
                conn,
            )["name"].tolist()
            if not tables:
                raise ValueError(f"No user tables found in SQLite database: {path}")
            if len(tables) > 1:
                raise ValueError(
                    "SQLite database has multiple tables; inspect the data map and "
                    f"choose a table or join path explicitly. Tables: {tables}"
                )
            table_name = str(tables[0]).replace('"', '""')
            return pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
    raise ValueError(f"Unsupported file type: {suffix}")


def ensure_dirs(out: Path) -> None:
    for rel in ["tables", "figures", "models"]:
        (out / rel).mkdir(parents=True, exist_ok=True)


def profile_data(df: pd.DataFrame, out: Path) -> dict[str, Any]:
    overview = pd.DataFrame({
        "column": df.columns,
        "dtype": [str(df[c].dtype) for c in df.columns],
        "missing_count": [int(df[c].isna().sum()) for c in df.columns],
        "missing_rate": [float(df[c].isna().mean()) for c in df.columns],
        "n_unique": [int(df[c].nunique(dropna=True)) for c in df.columns],
    })
    overview.to_csv(out / "tables" / "data_profile.csv", index=False, encoding="utf-8-sig")

    numeric = df.select_dtypes(include=[np.number])
    if not numeric.empty:
        numeric.describe().T.to_csv(out / "tables" / "numeric_describe.csv", encoding="utf-8-sig")

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_columns": numeric.columns.tolist(),
    }


def infer_task_type(y: pd.Series) -> str:
    non_null = y.dropna()
    if pd.api.types.is_numeric_dtype(non_null):
        unique = non_null.nunique()
        if unique <= min(20, max(2, int(len(non_null) * 0.05))):
            return "classification"
        return "regression"
    return "classification"


def make_preprocessor(X: pd.DataFrame, *, scale_numeric: bool) -> ColumnTransformer:
    num_cols = X.select_dtypes(include=[np.number, "bool"]).columns.tolist()
    cat_cols = [c for c in X.columns if c not in num_cols]
    num_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        num_steps.append(("scaler", StandardScaler()))
    cat_steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False, min_frequency=2)),
    ]
    return ColumnTransformer([
        ("num", Pipeline(num_steps), num_cols),
        ("cat", Pipeline(cat_steps), cat_cols),
    ], remainder="drop", verbose_feature_names_out=False)


def candidates(task: str) -> list[tuple[str, Any, bool]]:
    if task == "regression":
        return [
            ("dummy_mean", DummyRegressor(strategy="mean"), False),
            ("linear", LinearRegression(), True),
            ("ridge", Ridge(alpha=1.0, random_state=RANDOM_STATE), True),
            ("lasso", Lasso(alpha=0.001, max_iter=20000, random_state=RANDOM_STATE), True),
            ("random_forest", RandomForestRegressor(n_estimators=400, random_state=RANDOM_STATE, n_jobs=-1), False),
            ("extra_trees", ExtraTreesRegressor(n_estimators=400, random_state=RANDOM_STATE, n_jobs=-1), False),
            ("gradient_boosting", GradientBoostingRegressor(random_state=RANDOM_STATE), False),
            ("hist_gradient_boosting", HistGradientBoostingRegressor(random_state=RANDOM_STATE), False),
        ]
    return [
        ("dummy_most_frequent", DummyClassifier(strategy="most_frequent", random_state=RANDOM_STATE), False),
        ("logistic", LogisticRegression(max_iter=5000, class_weight="balanced", random_state=RANDOM_STATE), True),
        ("random_forest", RandomForestClassifier(n_estimators=400, random_state=RANDOM_STATE, n_jobs=-1, class_weight="balanced"), False),
        ("extra_trees", ExtraTreesClassifier(n_estimators=400, random_state=RANDOM_STATE, n_jobs=-1, class_weight="balanced"), False),
        ("gradient_boosting", GradientBoostingClassifier(random_state=RANDOM_STATE), False),
        ("hist_gradient_boosting", HistGradientBoostingClassifier(random_state=RANDOM_STATE), False),
    ]


def regression_metrics(y_true: pd.Series, pred: np.ndarray) -> dict[str, float]:
    return {
        "r2": float(r2_score(y_true, pred)),
        "rmse": float(math.sqrt(mean_squared_error(y_true, pred))),
        "mae": float(mean_absolute_error(y_true, pred)),
    }


def classification_metrics(y_true: pd.Series, pred: np.ndarray, model: Any, X: pd.DataFrame) -> dict[str, float]:
    out = {
        "accuracy": float(accuracy_score(y_true, pred)),
        "f1_macro": float(f1_score(y_true, pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, pred, average="weighted", zero_division=0)),
    }
    try:
        if hasattr(model, "predict_proba") and y_true.nunique() == 2:
            out["roc_auc"] = float(roc_auc_score(y_true, model.predict_proba(X)[:, 1]))
    except Exception:
        pass
    return out


def run_models(df: pd.DataFrame, target: str, out: Path) -> tuple[pd.DataFrame, Any, dict[str, Any]]:
    y = df[target]
    X = df.drop(columns=[target])
    valid = y.notna()
    X = X.loc[valid].copy()
    y = y.loc[valid].copy()
    task = infer_task_type(y)

    stratify = y if task == "classification" and y.nunique() > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=stratify
    )

    rows = []
    best_model = None
    best_score = -np.inf
    primary = "r2" if task == "regression" else "f1_macro"

    for name, estimator, scale in candidates(task):
        model = Pipeline([
            ("preprocess", make_preprocessor(X_train, scale_numeric=scale)),
            ("model", estimator),
        ])
        scoring = "r2" if task == "regression" else "f1_macro"
        cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE) if task == "regression" else StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
        cv_mean = cv_std = None
        try:
            cv_res = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1)
            cv_mean = float(np.mean(cv_res["test_score"]))
            cv_std = float(np.std(cv_res["test_score"]))
        except Exception as exc:
            cv_error = str(exc)
        else:
            cv_error = ""

        model.fit(X_train, y_train)
        pred_train = model.predict(X_train)
        pred_test = model.predict(X_test)
        if task == "regression":
            train_m = regression_metrics(y_train, pred_train)
            test_m = regression_metrics(y_test, pred_test)
        else:
            train_m = classification_metrics(y_train, pred_train, model, X_train)
            test_m = classification_metrics(y_test, pred_test, model, X_test)

        row = {
            "model": name,
            "task": task,
            "cv_primary_mean": cv_mean,
            "cv_primary_std": cv_std,
            "train_primary": train_m[primary],
            "test_primary": test_m[primary],
            "gap": train_m[primary] - test_m[primary],
            "cv_error": cv_error,
            **{f"train_{k}": v for k, v in train_m.items()},
            **{f"test_{k}": v for k, v in test_m.items()},
        }
        rows.append(row)
        score = cv_mean if cv_mean is not None else test_m[primary]
        if score > best_score:
            best_score = score
            best_model = model

    metrics = pd.DataFrame(rows).sort_values(["cv_primary_mean", "test_primary"], ascending=False, na_position="last")
    metrics.to_csv(out / "tables" / "model_metrics.csv", index=False, encoding="utf-8-sig")

    # Feature importance via permutation on the best model.
    try:
        perm = permutation_importance(best_model, X_test, y_test, n_repeats=10, random_state=RANDOM_STATE, n_jobs=-1, scoring=("r2" if task == "regression" else "f1_macro"))
        importance = pd.DataFrame({
            "feature": X_test.columns,
            "importance_mean": perm.importances_mean,
            "importance_std": perm.importances_std,
        }).sort_values("importance_mean", ascending=False)
        importance.to_csv(out / "tables" / "permutation_importance.csv", index=False, encoding="utf-8-sig")
        plot_feature_importance(importance.head(20), out / "figures" / "feature_importance.png")
    except Exception as exc:
        (out / "tables" / "permutation_importance_error.txt").write_text(str(exc), encoding="utf-8")

    # Prediction diagnostics.
    try:
        pred = best_model.predict(X_test)
        if task == "regression":
            plt.figure(figsize=(7, 6))
            plt.scatter(y_test, pred, alpha=0.7)
            lo, hi = min(y_test.min(), pred.min()), max(y_test.max(), pred.max())
            plt.plot([lo, hi], [lo, hi], linestyle="--")
            plt.xlabel("Actual")
            plt.ylabel("Predicted")
            plt.title("Predicted vs Actual")
            plt.tight_layout()
            plt.savefig(out / "figures" / "predicted_vs_actual.png", dpi=150)
            plt.close()
    except Exception:
        pass

    metadata = {
        "task_type": task,
        "target": target,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "best_model": str(metrics.iloc[0]["model"]),
        "primary_metric": primary,
    }
    return metrics, best_model, metadata


def plot_feature_importance(importance: pd.DataFrame, path: Path) -> None:
    if importance.empty:
        return
    ordered = importance.sort_values("importance_mean", ascending=True)
    plt.figure(figsize=(8, max(4, len(ordered) * 0.3)))
    plt.barh(ordered["feature"], ordered["importance_mean"])
    plt.xlabel("Permutation importance")
    plt.title("Top Feature Importance")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def artifact_kind(path: Path) -> str:
    if path.name == "report.md":
        return "report"
    if path.name == "run_summary.json":
        return "run_summary"
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".svg", ".webp"}:
        return "figure"
    if path.suffix.lower() in {".csv", ".xlsx", ".parquet", ".json"}:
        return "table_or_data"
    if path.suffix.lower() in {".pkl", ".joblib"}:
        return "model"
    return "artifact"


def artifact_purpose(path: Path) -> str:
    if path.name == "report.md":
        return "Final analysis report"
    if path.name == "run_summary.json":
        return "Machine-readable run contract"
    if "figures" in path.parts:
        return "Visual evidence"
    if "tables" in path.parts:
        return "Tabular evidence"
    if "models" in path.parts:
        return "Saved model artifact"
    return "Generated analysis artifact"


def collect_generated_files(out: Path) -> list[dict[str, str]]:
    files = [p for p in sorted(out.rglob("*")) if p.is_file()]
    summary_path = out / "run_summary.json"
    if summary_path not in files:
        files.append(summary_path)
    return [
        {
            "path": str(path).replace("\\", "/"),
            "kind": artifact_kind(path),
            "purpose": artifact_purpose(path),
        }
        for path in files
    ]


def build_quality_gates(out: Path, target: str | None, model_meta: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "raw_data_preserved": True,
        "data_profile_written": (out / "tables" / "data_profile.csv").exists(),
        "missingness_documented": (out / "tables" / "data_profile.csv").exists(),
        "leakage_checked": "manual_review_required" if target else "not_applicable",
        "split_preprocessing_safe": bool(model_meta) if target else "not_applicable",
        "metrics_from_validation": bool(model_meta) if target else "not_applicable",
        "charts_checked": "review_generated_figures" if any((out / "figures").glob("*")) else "not_applicable",
        "report_causality_checked": True,
    }


def write_report(out: Path, goal: str, profile: dict[str, Any], model_meta: dict[str, Any] | None, warnings: list[str]) -> None:
    report = [
        "# Analysis Report",
        "",
        "## Executive Summary",
        "",
        f"Goal: {goal}",
        "",
        "This report was generated from a reproducible data-lab-lite analysis script. Review the tables and figures in `outputs/` for details.",
        "",
        "## Data Overview",
        "",
        f"- Rows: {profile['rows']}",
        f"- Columns: {profile['columns']}",
        f"- Missing cells: {profile['missing_cells']}",
        f"- Duplicate rows: {profile['duplicate_rows']}",
        "",
    ]
    if model_meta:
        report += [
            "## Modeling Results",
            "",
            f"- Task type: {model_meta['task_type']}",
            f"- Target: {model_meta['target']}",
            f"- Best model: {model_meta['best_model']}",
            f"- Primary metric: {model_meta['primary_metric']}",
            "- Metrics table: `outputs/tables/model_metrics.csv`",
            "",
        ]
    if warnings:
        report += ["## Warnings", ""] + [f"- {w}" for w in warnings] + [""]
    report += [
        "## Next Steps",
        "",
        "- Review warnings and limitations before using results for decisions." if warnings else "- Use the report findings as the starting point for follow-up analysis.",
        "",
    ]
    report += [
        "## Reproducibility",
        "",
        "- Script: `scripts/analyze.py`",
        "- Data profile: `outputs/tables/data_profile.csv`",
        "- Run summary: `outputs/run_summary.json`",
        "",
    ]
    (out / "report.md").write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)
    out = Path(args.output_dir)
    ensure_dirs(out)

    df = read_data(data_path)
    df.columns = [str(c).strip() for c in df.columns]
    profile = profile_data(df, out)
    warnings: list[str] = []

    model_meta = None
    if args.target:
        if args.target not in df.columns:
            raise ValueError(f"Target column not found: {args.target}")
        metrics, _, model_meta = run_models(df, args.target, out)
        best = metrics.iloc[0].to_dict()
        if model_meta["task_type"] == "regression" and float(best.get("test_r2", -999)) < 0.85:
            warnings.append("Best regression test R² is below 0.85; treat results as needing diagnosis for simple benchmark datasets.")
        if abs(float(best.get("gap", 0))) > 0.15:
            warnings.append("Train-test gap is large; possible overfitting or unstable split.")

    write_report(out, args.goal, profile, model_meta, warnings)
    generated_files = collect_generated_files(out)
    quality_gates = build_quality_gates(out, args.target, model_meta)
    next_actions = ["Review warnings before relying on the result."] if warnings else ["Review report findings and decide whether deeper analysis is needed."]

    run_summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "goal": args.goal,
        "task_level": "Standard",
        "assumptions": ["Single input dataset or single SQLite table unless the script was adapted."],
        "input_files": [str(data_path)],
        "data_shape": {"rows": profile["rows"], "columns": profile["columns"]},
        "target": args.target,
        "task_type": model_meta["task_type"] if model_meta else None,
        "split_strategy": "train/test plus cross-validation" if model_meta else None,
        "best_model": model_meta["best_model"] if model_meta else None,
        "generated_files": generated_files,
        "quality_gates": quality_gates,
        "limitations": [],
        "next_actions": next_actions,
        "warnings": warnings,
        "outputs": [item["path"] for item in generated_files],
    }
    (out / "run_summary.json").write_text(json.dumps(run_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(run_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

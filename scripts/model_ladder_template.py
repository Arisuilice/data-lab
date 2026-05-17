#!/usr/bin/env python3
"""Reusable sklearn model ladder for small-to-medium tabular datasets.

This file is a template. Copy it into a project when supervised modeling is needed,
or adapt the functions directly inside scripts/analyze.py.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal

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

TaskType = Literal["regression", "classification"]


@dataclass
class ModelResult:
    name: str
    cv_primary_mean: float | None
    cv_primary_std: float | None
    train_primary: float
    test_primary: float
    secondary: dict[str, float]
    gap: float
    estimator: Any


def infer_task_type(y: pd.Series) -> TaskType:
    """Infer classification vs regression from target dtype and cardinality."""
    non_null = y.dropna()
    if non_null.empty:
        raise ValueError("Target column is empty after dropping missing values.")
    if pd.api.types.is_numeric_dtype(non_null):
        unique = non_null.nunique()
        if unique <= min(20, max(2, int(len(non_null) * 0.05))):
            return "classification"
        return "regression"
    return "classification"


def make_preprocessor(X: pd.DataFrame, *, scale_numeric: bool) -> ColumnTransformer:
    numeric_cols = X.select_dtypes(include=[np.number, "bool"]).columns.tolist()
    categorical_cols = [c for c in X.columns if c not in numeric_cols]

    numeric_steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))

    categorical_steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False, min_frequency=2)),
    ]

    return ColumnTransformer(
        transformers=[
            ("num", Pipeline(numeric_steps), numeric_cols),
            ("cat", Pipeline(categorical_steps), categorical_cols),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def model_candidates(task_type: TaskType, random_state: int = 42) -> list[tuple[str, Any, bool]]:
    """Return (name, estimator, scale_numeric)."""
    if task_type == "regression":
        return [
            ("dummy_mean", DummyRegressor(strategy="mean"), False),
            ("linear", LinearRegression(), True),
            ("ridge", Ridge(alpha=1.0, random_state=random_state), True),
            ("lasso", Lasso(alpha=0.001, max_iter=20000, random_state=random_state), True),
            ("random_forest", RandomForestRegressor(n_estimators=500, random_state=random_state, n_jobs=-1), False),
            ("extra_trees", ExtraTreesRegressor(n_estimators=500, random_state=random_state, n_jobs=-1), False),
            ("gradient_boosting", GradientBoostingRegressor(random_state=random_state), False),
            ("hist_gradient_boosting", HistGradientBoostingRegressor(random_state=random_state), False),
        ]
    return [
        ("dummy_most_frequent", DummyClassifier(strategy="most_frequent", random_state=random_state), False),
        ("logistic", LogisticRegression(max_iter=5000, class_weight="balanced", random_state=random_state), True),
        ("random_forest", RandomForestClassifier(n_estimators=500, random_state=random_state, n_jobs=-1, class_weight="balanced"), False),
        ("extra_trees", ExtraTreesClassifier(n_estimators=500, random_state=random_state, n_jobs=-1, class_weight="balanced"), False),
        ("gradient_boosting", GradientBoostingClassifier(random_state=random_state), False),
        ("hist_gradient_boosting", HistGradientBoostingClassifier(random_state=random_state), False),
    ]


def evaluate_regression(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    rmse = math.sqrt(mean_squared_error(y_true, y_pred))
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "rmse": float(rmse),
        "mae": float(mean_absolute_error(y_true, y_pred)),
    }


def evaluate_classification(y_true: pd.Series, y_pred: np.ndarray, estimator: Any, X: pd.DataFrame) -> dict[str, float]:
    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }
    try:
        if hasattr(estimator, "predict_proba") and y_true.nunique() == 2:
            proba = estimator.predict_proba(X)[:, 1]
            out["roc_auc"] = float(roc_auc_score(y_true, proba))
    except Exception:
        pass
    return out


def run_model_ladder(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    task_type: TaskType | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
    cv_folds: int = 5,
) -> tuple[pd.DataFrame, Any, dict[str, Any]]:
    """Train a small but strong model ladder and return metrics, best estimator, metadata."""
    task_type = task_type or infer_task_type(y)

    valid = y.notna()
    X = X.loc[valid].copy()
    y = y.loc[valid].copy()

    stratify = y if task_type == "classification" and y.nunique() > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify
    )

    rows: list[dict[str, Any]] = []
    best_estimator = None
    best_score = -np.inf

    for name, model, scale_numeric in model_candidates(task_type, random_state=random_state):
        pipe = Pipeline([
            ("preprocess", make_preprocessor(X_train, scale_numeric=scale_numeric)),
            ("model", model),
        ])

        scoring = "r2" if task_type == "regression" else "f1_macro"
        cv = (
            KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
            if task_type == "regression"
            else StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
        )

        cv_mean = cv_std = None
        try:
            cv_res = cross_validate(pipe, X_train, y_train, scoring=scoring, cv=cv, n_jobs=-1, return_train_score=True)
            cv_mean = float(np.mean(cv_res["test_score"]))
            cv_std = float(np.std(cv_res["test_score"]))
        except Exception:
            pass

        pipe.fit(X_train, y_train)
        pred_train = pipe.predict(X_train)
        pred_test = pipe.predict(X_test)

        if task_type == "regression":
            train_metrics = evaluate_regression(y_train, pred_train)
            test_metrics = evaluate_regression(y_test, pred_test)
            primary = "r2"
        else:
            train_metrics = evaluate_classification(y_train, pred_train, pipe, X_train)
            test_metrics = evaluate_classification(y_test, pred_test, pipe, X_test)
            primary = "f1_macro"

        train_primary = train_metrics[primary]
        test_primary = test_metrics[primary]
        gap = train_primary - test_primary

        row = {
            "model": name,
            "task_type": task_type,
            "cv_primary_mean": cv_mean,
            "cv_primary_std": cv_std,
            "train_primary": train_primary,
            "test_primary": test_primary,
            "gap": gap,
            **{f"test_{k}": v for k, v in test_metrics.items()},
            **{f"train_{k}": v for k, v in train_metrics.items()},
        }
        rows.append(row)

        score_for_selection = cv_mean if cv_mean is not None else test_primary
        if score_for_selection > best_score:
            best_score = score_for_selection
            best_estimator = pipe

    metrics = pd.DataFrame(rows).sort_values(
        by=["cv_primary_mean", "test_primary"], ascending=False, na_position="last"
    )
    metadata = {
        "task_type": task_type,
        "test_size": test_size,
        "random_state": random_state,
        "cv_folds": cv_folds,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "selection_score": float(best_score),
    }
    return metrics, best_estimator, metadata

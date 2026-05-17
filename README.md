# data-lab-lite

<p align="center">
  <strong>Lightweight, reproducible data analysis for agents.</strong>
</p>

<p align="center">
  <a href="#quick-start"><img alt="Quick Start" src="https://img.shields.io/badge/workflow-quick%20start-2f6fed?style=flat-square"></a>
  <a href="#quality-gates"><img alt="Quality Gates" src="https://img.shields.io/badge/quality-strong%20baselines-20a67a?style=flat-square"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-111827?style=flat-square"></a>
</p>

`data-lab-lite` is a compact data-analysis Skill for CSV, Excel, JSON, Parquet, SQLite, and other small-to-medium tabular datasets. It helps an agent move from raw data to defensible results without turning a simple analysis into a heavyweight workflow.

It is designed around one practical rule:

> Use the smallest sufficient process to answer the real question, run strong baselines, produce reproducible scripts, and write a clear report.

## Highlights

| What it optimizes for | How it shows up |
|---|---|
| Correct answers | Data profiling, leakage checks, appropriate metrics, and explicit limitations |
| Strong baselines | Dummy, linear, tree-based, and boosting models before interpretation |
| Reproducibility | Minimal project structure, reusable templates, and `run_summary.json` |
| Clear reporting | Concise findings, evidence-backed conclusions, and next-step recommendations |
| Lightweight execution | One main script by default; larger workflows only when the task truly needs them |

## When To Use

Use this Skill when a user provides data and asks for:

- data exploration, profiling, field understanding, or cleaning;
- missing-value handling, outlier checks, or data quality review;
- correlation, group differences, segmentation, drivers, or explanatory analysis;
- regression, classification, clustering, prediction, ranking, or time-series modeling;
- visualizations, tables, reproducible scripts, or an analysis report.

If the user only asks a conceptual or methodological question and does not provide data, answer directly instead of creating a project.

## Repository Layout

```text
data-lab-lite/
├── SKILL.md
├── README.md
├── assets/
│   ├── report-template.md
│   └── run-summary-schema.json
├── references/
│   ├── data-analysis-playbook.md
│   ├── failure-modes.md
│   ├── modeling-playbook.md
│   ├── report-guide.md
│   ├── routing.md
│   ├── statistics-playbook.md
│   ├── usage.md
│   └── visualization-guide.md
└── scripts/
    ├── analyze_template.py
    ├── bootstrap_project.py
    └── model_ladder_template.py
```

## Quick Start

Copy this folder into your Codex skills directory, for example:

```text
~/.codex/skills/data-lab-lite/
```

For a minimal analysis project, initialize the structure:

```bash
python scripts/bootstrap_project.py --project-root ./analysis_project --data ./data.csv
```

Then adapt the analysis template:

```bash
cp scripts/analyze_template.py ./analysis_project/scripts/analyze.py
python ./analysis_project/scripts/analyze.py \
  --data ./analysis_project/data/raw/data.csv \
  --target TARGET_COLUMN \
  --output-dir ./analysis_project/outputs
```

The template is meant to be edited for the actual dataset and question. It is a starting point, not a rigid pipeline.

## Workflow

```mermaid
flowchart LR
  A["Load data"] --> B["Profile fields"]
  B --> C["Clean minimally"]
  C --> D["Run baselines"]
  D --> E["Improve deliberately"]
  E --> F["Interpret carefully"]
  F --> G["Report clearly"]
```

The default route is `Standard`: one dataset, one target or research direction, one main script, and one report. Escalate only when the task has multiple independent goals, multiple data sources, long-running collaboration needs, or production/audit requirements.

## Task Levels

| Level | Best for | Default output |
|---|---|---|
| Quick | One local question or small file | Inline answer, one table, or one chart |
| Standard | One dataset and one analysis goal | `scripts/analyze.py` plus `outputs/report.md` |
| Expanded | Several independent questions or targets | 2-5 focused scripts |
| Project | Long-term, audited, or multi-round work | A fuller project structure with checkpoints only when justified |

## Quality Gates

Before considering an analysis complete, this Skill expects:

- original data preserved;
- missing values, dropped rows, and dropped columns documented;
- train/test preprocessing fit only on the training split;
- at least one naive baseline and one strong nonlinear baseline for supervised learning;
- metrics taken from validation, test, or cross-validation;
- charts with readable labels, titles, units, and working CJK font handling when needed;
- reports that distinguish prediction, correlation, statistical significance, and causality.

## What It Avoids

`data-lab-lite` intentionally avoids heavy process artifacts unless the task demands them:

```text
state.json
analysis_units.json
analysis_dag.json
metrics_catalog.json
evidence_registry.json
multi-level checkpoint directories
multi-level review registries
```

The goal is not to look complex. The goal is to be right, reproducible, and useful.

## Dependencies

Default dependencies:

```text
pandas numpy matplotlib scikit-learn scipy statsmodels openpyxl pyarrow
```

Optional dependencies, only when useful:

```text
xgboost lightgbm shap seaborn duckdb polars
```

## License

MIT License. See `SKILL.md` metadata for the declared license.

# data-lab-lite

<p align="center">
  <a href="README.md">English</a> | <strong>简体中文</strong>
</p>

<p align="center">
  <strong>面向 Agent 的轻量、可复现数据分析 Skill。</strong>
</p>

<p align="center">
  <a href="#快速开始"><img alt="快速开始" src="https://img.shields.io/badge/workflow-快速开始-2f6fed?style=flat-square"></a>
  <a href="#质量门"><img alt="质量门" src="https://img.shields.io/badge/quality-强基线-20a67a?style=flat-square"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-111827?style=flat-square"></a>
</p>

`data-lab-lite` 是一个紧凑的数据分析 Skill，适用于 CSV、Excel、JSON、Parquet、SQLite 以及其他中小型表格数据。它帮助 Agent 从原始数据推进到可靠结论，同时避免把简单分析变成重型流水线。

它围绕一个实用原则设计：

> 用最小但足够的流程，回答真实问题，运行强基线，产出可复现脚本，并写出清晰报告。

## 核心特性

| 优先优化 | 具体体现 |
|---|---|
| 正确回答 | 数据画像、泄漏检查、合适指标和明确限制 |
| 强基线 | 解释前先比较 Dummy、线性、树模型与 boosting 模型 |
| 可复现 | 最小项目结构、可复用模板和 `run_summary.json` |
| 清晰报告 | 简洁发现、有证据支撑的结论和下一步建议 |
| 轻量执行 | 默认一个主脚本；只有任务真正需要时才升级流程 |

## 何时使用

当用户提供数据并提出以下需求时，使用这个 Skill：

- 数据探索、数据画像、字段理解或清洗；
- 缺失值处理、异常值检查或数据质量审查；
- 相关性、组间差异、分群、驱动因素或解释性分析；
- 回归、分类、聚类、预测、排序或时间序列建模；
- 图表、表格、可复现脚本或分析报告。

如果用户只是询问概念或方法，且没有提供数据，直接回答即可，不必创建项目。

## 仓库结构

```text
data-lab-lite/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── report-template.md
│   └── run-summary-schema.json
├── references/
│   ├── data-analysis-playbook.md
│   ├── execution-loop.md
│   ├── failure-modes.md
│   ├── modeling-playbook.md
│   ├── multi-source-playbook.md
│   ├── report-guide.md
│   ├── routing.md
│   ├── statistics-playbook.md
│   ├── usage.md
│   └── visualization-guide.md
└── scripts/
    ├── analyze_template.py
    ├── bootstrap_project.py
    ├── model_ladder_template.py
    └── validate_run.py
```

## 快速开始

将此文件夹复制到 Codex skills 目录，例如：

```text
~/.codex/skills/data-lab-lite/
```

初始化一个最小分析项目：

```bash
python scripts/bootstrap_project.py --project-root ./analysis_project --data ./data.csv
```

然后改写分析模板：

```bash
cp scripts/analyze_template.py ./analysis_project/scripts/analyze.py
python ./analysis_project/scripts/analyze.py \
  --data ./analysis_project/data/raw/data.csv \
  --target TARGET_COLUMN \
  --output-dir ./analysis_project/outputs
```

验证生成的运行契约和核心产物：

```bash
python scripts/validate_run.py --project-root ./analysis_project
```

模板应该根据实际数据和问题调整。它是起点，不是僵硬流水线。

## 工作流

```mermaid
flowchart LR
  A["读取数据"] --> B["字段画像"]
  B --> C["最小清洗"]
  C --> D["运行基线"]
  D --> E["有理由地改进"]
  E --> F["谨慎解释"]
  F --> G["清晰报告"]
```

默认路线是 `Standard`：一个数据集、一个目标或研究方向、一个主脚本和一份报告。只有在任务包含多个独立目标、多数据源、长期协作或生产审计需求时，才升级流程。

`2.2.0-lite` 额外加入一个轻量工作区契约：每次 Standard 运行都应在 `outputs/run_summary.json` 中记录输入、生成产物、质量门、警告、限制和下一步动作。

## 任务级别

| 级别 | 适用场景 | 默认产物 |
|---|---|---|
| Quick | 一个局部问题或小文件 | 对话内答案、一张表或一张图 |
| Standard | 一个数据集和一个分析目标 | `scripts/analyze.py` 加 `outputs/report.md` |
| Expanded | 多个独立问题或目标变量 | 2-5 个聚焦脚本 |
| Project | 长期、多轮、审计或协作项目 | 仅在必要时创建更完整结构和 checkpoint |

## 质量门

在认为分析完成之前，这个 Skill 要求检查：

- 原始数据已保留；
- 缺失值、删除行和删除列有记录；
- train/test 拆分下的预处理只在训练集 fit；
- 监督学习至少包含一个 naive baseline 和一个强非线性 baseline；
- 指标来自验证集、测试集或交叉验证；
- 图表有可读标签、标题、单位，并在需要时正确处理 CJK 字体；
- 报告明确区分预测、相关、统计显著性和因果结论。
- `outputs/run_summary.json` 包含 `task_level`、`generated_files`、`quality_gates` 和 `next_actions`；
- `scripts/validate_run.py --project-root <project>` 能发现缺失报告或摘要字段。

## 它刻意避免什么

除非任务确实需要，`data-lab-lite` 不默认创建重型流程产物：

```text
state.json
analysis_units.json
analysis_dag.json
metrics_catalog.json
evidence_registry.json
multi-level checkpoint directories
multi-level review registries
```

目标不是显得复杂，而是正确、可复现、可行动。

## 依赖

默认依赖：

```text
pandas numpy matplotlib scikit-learn scipy statsmodels openpyxl pyarrow
```

可选依赖，仅在确实有用时使用：

```text
xgboost lightgbm shap seaborn duckdb polars
```

## 许可证

MIT License。详见 `LICENSE`。

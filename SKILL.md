---
name: data-lab-lite
description: >
  快速、实用、结果导向的数据分析 Skill。用户提供 CSV、Excel、JSON、Parquet、SQLite
  或中小型表格数据，并要求数据探索、清洗、统计分析、机器学习建模、可视化或分析报告时使用。
  优先级是正确回答、强基线、可复现脚本和清晰报告；避免为简单任务创建重型流水线。
version: 2.1.0-lite
author: Arisuilice
license: MIT
metadata:
  pattern: tool-wrapper + generator + lightweight-reviewer
  domain: data-analysis
  priority: efficiency-and-quality
  min_context_window: 32000
  supported_input_formats:
    - csv / tsv
    - xlsx / xls
    - json / jsonl
    - parquet / feather
    - sqlite
    - fixed-width / text with delimiter
---

# data-lab-lite

## 0. 一句话原则

用最少必要流程，把数据问题答对、模型跑强、结论写清楚。

优先级固定为：

1. 回答用户真实问题；
2. 使用足够强的经验基线，尤其是建模任务；
3. 生成可复现脚本；
4. 写出清楚、克制、可行动的报告；
5. 只保留必要产物。

不要把简单分析变成大型工作流。默认不创建状态机、DAG、多阶段 gate、AU 分片、checkpoint 系统或 evidence registry。只有任务真的需要长期协作、生产审计或复杂多目标并行时才升级。

---

## 1. 何时使用

当用户提供数据并提出以下任一需求时使用本 Skill：

- 数据探索、数据画像、字段理解；
- 数据清洗、缺失处理、异常识别；
- 相关性、差异、分群、驱动因素、解释性分析；
- 回归、分类、聚类、预测、排序、时间序列等建模；
- 图表、表格、分析报告、可复现脚本。

若用户只是问概念问题、方法解释或不提供数据，不必创建项目，直接回答。

---

## 2. 文件地图与按需加载

本 Skill 使用渐进式披露：先读本文件，只在需要时加载 references。

```text
data-lab-lite/
├── SKILL.md
├── README.md
├── references/
│   ├── routing.md                  # 任务分级、何时拆分、何时升级
│   ├── data-analysis-playbook.md   # 读取、清洗、EDA、字段处理
│   ├── modeling-playbook.md        # 监督/无监督建模强基线与指标
│   ├── statistics-playbook.md      # 统计检验、效应量、交互项解释
│   ├── visualization-guide.md      # 图表规范、中文字体、可读性检查
│   ├── report-guide.md             # 报告结构与表达边界
│   └── failure-modes.md            # 常见失败模式与修复动作
├── scripts/
│   ├── bootstrap_project.py        # 创建最小项目结构
│   ├── analyze_template.py         # 单脚本分析模板
│   └── model_ladder_template.py    # 强基线模型梯队模板
└── assets/
    ├── report-template.md          # 默认报告模板
    └── run-summary-schema.json     # run_summary.json 建议结构
```

按需加载规则：

| 场景 | 必读 |
|---|---|
| 任何数据文件分析 | `references/routing.md`, `references/data-analysis-playbook.md` |
| 监督学习 / 预测建模 | `references/modeling-playbook.md`, `scripts/model_ladder_template.py` |
| 显著性、相关、回归解释 | `references/statistics-playbook.md` |
| 需要图表 | `references/visualization-guide.md` |
| 需要正式报告 | `references/report-guide.md`, `assets/report-template.md` |
| 结果差、乱码、耗时异常、结论牵强 | `references/failure-modes.md` |

---

## 3. 任务分级

执行前先判断复杂度，选择最轻的充分流程。

| 级别 | 条件 | 默认做法 |
|---|---|---|
| Quick | 一个文件、一个简单问题、不要求正式报告 | 直接分析；必要时只输出表格/图 |
| Standard | 一个数据集、一个目标或研究方向、要求报告 | 一个 `scripts/analyze.py` + `outputs/report.md` |
| Expanded | 多目标、多问题、多数据源，但仍是一次性任务 | 2-5 个脚本，按问题或目标拆分 |
| Project | 长期、多轮、生产审计、复杂依赖、可回滚要求 | 才创建更完整项目结构和 checkpoint |

默认 Standard。不要因为“看起来专业”而升级。

---

## 4. 最小项目结构

Standard 任务只创建：

```text
project/
├── data/
│   ├── raw/                 # 原始数据，只读
│   └── processed/           # 可选：清洗后数据
├── scripts/
│   └── analyze.py           # 主分析脚本
└── outputs/
    ├── report.md            # 最终报告
    ├── run_summary.json     # 指标、文件、警告、假设
    ├── tables/              # 关键表格
    ├── figures/             # 关键图表
    └── models/              # 可选模型文件
```

默认禁止生成以下重型文件：

```text
state.json
analysis_units.json
analysis_dag.json
metrics_catalog.json
evidence_registry.json
checkpoint 多级目录
review 多级审计目录
```

除非用户明确要求可审计流水线，或任务达到 Project 级别。

---

## 5. 默认执行流程

### 5.1 不过度追问

如果目标足够清楚，直接执行。只有在目标变量、预测对象或交付格式完全无法判断时，才问一个澄清问题。若可以合理假设，先声明假设再继续。

### 5.2 先建立数据认知

必须检查：

- 数据规模、字段、类型、样本；
- 缺失、重复、异常、极端值；
- 目标变量分布；
- 类别基数、日期字段、文本字段；
- 可能的目标泄漏字段；
- 数据是否存在截尾、审查、采样偏差或明显历史语境。

### 5.3 先强基线，后解释

建模任务不能只跑 OLS 或单个模型。

回归至少比较：

1. DummyRegressor；
2. Linear / Ridge / Lasso；
3. RandomForest / ExtraTrees；
4. GradientBoosting / HistGradientBoosting；
5. 必要时对最强模型做轻量调参。

分类至少比较：

1. DummyClassifier；
2. LogisticRegression / LinearSVC；
3. RandomForest / ExtraTrees；
4. GradientBoosting / HistGradientBoosting；
5. 必要时处理类别不平衡并调参。

OLS 是解释工具，不是预测性能上限。

### 5.4 小循环提升

若性能明显低于预期，最多执行 3 轮针对性提升：

1. 判断瓶颈：欠拟合、过拟合、泄漏风险、异常值、非线性、类别高基数、类别不平衡、缺失；
2. 只做一个有理由的改进；
3. 用同一验证方式重新评估；
4. 记录提升是否有效。

不要盲目堆几十个模型。

### 5.5 解释与报告

报告必须直接回答用户问题，并明确区分：

- 预测性能；
- 相关关系；
- 统计显著性；
- 因果结论。

非因果设计不得写成因果结论。

---

## 6. 轻量质量门

完成前检查以下事项。

### 6.1 数据门

- 原始数据未被覆盖；
- 删除行/列有记录；
- 缺失处理有说明；
- 建模任务考虑了目标泄漏；
- train/test split 下的预处理只在训练集 fit。

### 6.2 建模门

监督学习必须满足：

- 至少有一个 naive baseline；
- 至少有一个强非线性 baseline；
- 指标来自验证集、测试集或交叉验证，而不只是训练集；
- 指标匹配任务；
- 检查 train-test gap；
- 性能弱时必须直接说明，并至少做一次诊断。

警戒线：

| 任务 | 警戒条件 |
|---|---|
| 普通表格回归 | best validation R² < 0.70 |
| 简单 benchmark 回归 | 强非线性模型后 R² < 0.85 |
| 分类 | 只报 accuracy，不报类别分布/F1/AUC 等 |
| 类别不平衡 | 未报告 precision/recall/F1/PR-AUC |

警戒线不是造高分的理由，而是触发诊断的理由。

### 6.3 图表门

- 每张图有标题、坐标轴、单位；
- 中文图表必须检查字体渲染；
- 中文乱码不能通过，必须切换 CJK 字体或英文标签；
- 不生成不支持发现的装饰性图。

### 6.4 报告门

- 不把相关关系写成因果；
- 不用流程完整性掩盖弱模型；
- 不隐藏关键限制；
- 不输出与图表/指标矛盾的结论；
- 给出下一步建议。

---

## 7. 何时拆脚本

一个脚本是默认且推荐的。只有以下情况才拆：

- 多个独立目标变量；
- 超过 3 个独立研究问题；
- 多数据源且清洗逻辑不同；
- 单脚本预计超过 400-500 行；
- 某个分析失败不应影响其他分析；
- 运行耗时或调试复杂度明显上升。

拆分时只用简单命名：

```text
scripts/
├── 01_profile.py
├── 02_model.py
├── 03_interpret.py
└── run_all.py
```

`run_all.py` 可以调度，但不需要 DAG。

---

## 8. 依赖策略

默认依赖：

```text
pandas numpy matplotlib scikit-learn scipy statsmodels openpyxl pyarrow
```

可选依赖，仅在确实有用时安装/使用：

```text
xgboost lightgbm shap seaborn duckdb polars
```

优先使用 sklearn 内置方法。不要为了“看起来高级”增加依赖。

---

## 9. 成功标准

一次 data-lab-lite 任务成功，当且仅当：

1. 用户问题被直接回答；
2. 分析方法与问题匹配；
3. 建模任务比较了简单基线与强模型；
4. 结论有指标、图表或统计证据支撑；
5. 报告说明已知、未知、限制与下一步；
6. 产物数量与任务复杂度相称。

速度和效果优先于程序性完整。

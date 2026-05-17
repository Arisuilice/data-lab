# usage

`data-lab-lite` 是一个轻量、结果导向的数据分析 Skill。它用于替代重型多阶段 data-lab 流水线，适合大多数一次性数据分析、建模、可视化和报告任务。

## 设计目标

- 少问、快做、结果优先；
- 不用流程完整性掩盖低质量分析；
- 默认一个主脚本 + 一份报告；
- 建模任务必须跑强基线；
- 报告克制、可复现、直接回答问题。

## 安装

将整个文件夹放到 Skills 目录，例如：

```text
~/.claude/skills/data-lab-lite/
```

或在你的 Agent/CLI 支持的 skills 目录中使用同名文件夹。

## 文件说明

```text
SKILL.md                         主指令
references/routing.md            任务分级与拆分规则
references/data-analysis-playbook.md  数据读取、清洗、EDA
references/modeling-playbook.md       建模强基线与评估
references/statistics-playbook.md     统计分析和交互解释
references/visualization-guide.md     图表规范与中文字体检查
references/report-guide.md            报告写作规范
references/failure-modes.md           常见失败模式
scripts/bootstrap_project.py           最小项目初始化脚本
scripts/analyze_template.py            单脚本分析模板
scripts/model_ladder_template.py       模型梯队模板
assets/report-template.md              报告模板
assets/run-summary-schema.json         run_summary.json 建议结构
```

## 推荐工作方式

多数任务使用：

```text
python scripts/bootstrap_project.py --project-root ./analysis_project --data /path/to/data.csv
cp scripts/analyze_template.py ./analysis_project/scripts/analyze.py
# 根据用户目标修改 analyze.py，然后运行
python ./analysis_project/scripts/analyze.py --data ./analysis_project/data/raw/data.csv --target TARGET
```

实际使用时，Agent 可以直接生成更贴合当前数据的 `scripts/analyze.py`，不必机械复制模板。

## 什么时候不要升级成复杂项目

- 一个 CSV，一个目标变量；
- 一份课程作业报告；
- 一次性问卷分析；
- 经典机器学习数据集；
- 用户只需要“看明白数据、跑出结果、写出报告”。

这些场景默认不需要 state、DAG、AU、checkpoint 或 review registry。

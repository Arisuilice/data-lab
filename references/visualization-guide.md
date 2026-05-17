# visualization-guide

## 1. 图表原则

图表必须服务于发现。不要生成装饰性图。

每张图必须有：

- 标题；
- x/y 轴标签；
- 单位；
- 图例，如有多系列；
- 可读 tick label；
- 保存路径。

默认使用 matplotlib。可选 seaborn，但不要强依赖。

## 2. 常用图选择

| 目的 | 图表 |
|---|---|
| 分布 | histogram / density / boxplot |
| 两数值关系 | scatter + trend line |
| 类别比较 | bar chart / boxplot / violin |
| 模型误差 | residual plot / predicted vs actual |
| 特征重要性 | horizontal bar chart |
| 相关矩阵 | heatmap |
| 时间变化 | line chart |

## 3. 中文字体

生成中文图前必须检查可用字体。推荐顺序：

```python
candidate_fonts = [
    "Noto Sans CJK SC", "Noto Sans CJK JP", "Microsoft YaHei",
    "SimHei", "PingFang SC", "Heiti SC", "Arial Unicode MS"
]
```

若找不到 CJK 字体：

1. 图表标题与轴标签改为英文；
2. 报告正文可用中文解释；
3. 不允许输出中文乱码图。

## 4. 保存规范

- 默认 PNG；
- DPI 150，报告图可 300；
- 文件名使用英文小写与下划线；
- 同一图不要重复保存多个版本；
- 图中不要塞过多文字。

## 5. 模型图最小集

回归：

- predicted vs actual；
- residual distribution；
- top feature importance。

分类：

- confusion matrix；
- ROC/PR curve，如适用；
- top feature importance。

解释性回归：

- 关键变量关系图；
- 交互项边际效应图；
- 残差诊断图。

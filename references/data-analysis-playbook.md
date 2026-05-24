# data-analysis-playbook

## 1. 数据读取

优先使用 pandas。按扩展名读取：

| 格式 | 方法 |
|---|---|
| csv/tsv | `pd.read_csv`，必要时检测编码与分隔符 |
| xlsx/xls | `pd.read_excel` |
| json/jsonl | `pd.read_json` |
| parquet/feather | `pd.read_parquet` / `pd.read_feather` |
| sqlite | `sqlite3` + `pd.read_sql_query` |
| fwf/fixed-width | `pd.read_fwf` |

读取后必须记录：

- 行列数；
- 字段名；
- dtype；
- 前 5 行样本；
- 内存占用；
- 读取假设和警告。

SQLite 读取规则：

- 单表数据库可直接读取该表；
- 多表数据库先读 `multi-source-playbook.md`，不要盲目选择第一个表；
- 忽略 `sqlite_` 开头的内部表；
- 如果用户给出 SQL 或表名，优先使用用户指定内容。

固定宽度文本默认用 `.fwf` 扩展名识别。`.txt` 默认仍按分隔符文本读取；只有字段位置固定且分隔符解析失败时才切换 `read_fwf`。

## 2. 字段标准化

只做低风险标准化：

- 去除字段名前后空格；
- 统一重复字段名；
- 识别明显日期字段；
- 识别数值列中混入的字符串；
- 保留原始数据，不覆盖。

不要在没有理由的情况下重命名大量字段。

## 3. 缺失值

必须输出缺失表：

| column | missing_count | missing_rate | dtype | suggested_action |
|---|---:|---:|---|---|

处理原则：

- EDA 中可以保留缺失；
- 建模中用 Pipeline 内 imputer；
- 不要在 split 前对全量数据 fit imputer/scaler/encoder；
- 删除行/列必须报告影响比例。

## 4. 重复与异常

检查：

- 全行重复；
- 主键重复，若存在主键；
- 数值极端值；
- 目标变量截尾、封顶或明显离群；
- 类别字段拼写变体；
- 日期范围异常。

异常值默认不删除，除非：

- 明显录入错误；
- 用户目标要求清洗；
- 删除对结论影响很小并被记录。

## 5. EDA 最小集

至少生成：

- 数据概况表；
- 缺失表；
- 数值字段描述统计；
- 类别字段 top values；
- 目标变量分布；
- 与目标相关的主要字段关系。

## 6. 特征处理

轻量特征工程优先：

- 日期拆年/月/星期；
- 文本长度、是否为空；
- 合理 log transform；
- 交互项只在有解释理由时加入；
- 高基数类别先做频次合并或交给模型 pipeline。

不要大量生成不可解释特征，除非目标是纯预测且验证有效。

## 7. 泄漏检查

建模前检查：

- 字段名含 target、label、result、outcome、score、after、future、post 等；
- 时间上发生在预测点之后的字段；
- 由目标计算出的比例、排名、分组统计；
- ID 类字段是否记忆训练样本；
- 重复样本是否跨 train/test。

发现疑似泄漏时，先排除或单独报告，不要混入主模型。

# modeling-playbook

## 1. 核心原则

建模任务的第一目标是可信泛化性能，不是让训练集指标好看。

必须比较：

- naive baseline；
- 简单可解释模型；
- 强非线性模型；
- 必要时轻量调参。

## 2. 切分策略

| 数据类型 | 推荐切分 |
|---|---|
| 普通 IID 表格 | train/test 或 KFold CV |
| 小样本 | Repeated KFold 或 LOOCV，视规模而定 |
| 分类且类别不平衡 | Stratified split / StratifiedKFold |
| 时间序列 | 时间切分，禁止随机切分 |
| 分组样本 | GroupKFold / GroupShuffleSplit |

随机种子默认 42，并记录。

## 3. 回归模型梯队

必须至少尝试：

1. DummyRegressor；
2. LinearRegression 或 Ridge；
3. Lasso 或 ElasticNet；
4. RandomForestRegressor；
5. ExtraTreesRegressor；
6. HistGradientBoostingRegressor 或 GradientBoostingRegressor。

指标：

- R²；
- RMSE；
- MAE；
- train/test gap。

如用户关心解释，补充 statsmodels OLS 或 permutation importance。

## 4. 分类模型梯队

必须至少尝试：

1. DummyClassifier；
2. LogisticRegression；
3. RandomForestClassifier；
4. ExtraTreesClassifier；
5. HistGradientBoostingClassifier 或 GradientBoostingClassifier。

指标：

- accuracy；
- macro F1；
- weighted F1；
- ROC-AUC（二分类或可行时）；
- PR-AUC（类别不平衡时）；
- confusion matrix。

## 5. 无监督任务

聚类/降维不能强行给“好坏标签”。

最低要求：

- 数据标准化；
- 多个 k 或多个算法比较；
- silhouette / Davies-Bouldin / Calinski-Harabasz；
- 画像每个群体的特征差异；
- 明确说明聚类是探索性结果。

## 6. 低性能诊断

若模型低于警戒线，依次检查：

1. 目标是否噪声大或被截尾；
2. 是否缺关键特征；
3. 线性模型是否欠拟合；
4. 树模型是否过拟合；
5. 是否存在异常值主导指标；
6. 类别变量是否处理不当；
7. 数据量是否不足；
8. 切分方式是否不合适。

不要直接把低性能包装成“已通过”。

## 7. 解释方法

优先级：

1. permutation importance；
2. 模型内置 feature importance；
3. 线性模型系数，仅在标准化/编码解释清楚时使用；
4. PDP / ICE，用于解释非线性主效应；
5. SHAP 仅在依赖可用且任务值得时使用。

## 8. 报告模型结果

模型结果表建议包含：

| model | cv_r2/score | test_r2/score | rmse/mae/f1 | train_score | gap | notes |
|---|---:|---:|---:|---:|---:|---|

必须说明最佳模型为什么被选中：性能、稳定性、可解释性或业务约束。

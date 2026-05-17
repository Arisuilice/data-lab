# {{report_title}}

> Dataset: {{dataset_name}}  
> Goal: {{goal}}  
> Generated: {{generated_at}}  
> Script: {{script_path}}  
> Random seed: {{random_seed}}

---

## Executive Summary

{{executive_summary}}

---

## 1. Data Overview

- Rows: {{n_rows}}
- Columns: {{n_columns}}
- Target: {{target}}
- Missingness: {{missing_summary}}
- Key data warnings: {{data_warnings}}

---

## 2. Method

{{method_summary}}

For modeling tasks, include:

| Model | Validation/Test Score | Secondary Metric | Train Score | Gap | Notes |
|---|---:|---:|---:|---:|---|
| {{model}} | {{score}} | {{secondary_metric}} | {{train_score}} | {{gap}} | {{notes}} |

---

## 3. Results

### Finding 1: {{finding_1_title}}

- Evidence: {{finding_1_evidence}}
- Meaning: {{finding_1_meaning}}
- Limitation: {{finding_1_limitation}}

### Finding 2: {{finding_2_title}}

- Evidence: {{finding_2_evidence}}
- Meaning: {{finding_2_meaning}}
- Limitation: {{finding_2_limitation}}

### Finding 3: {{finding_3_title}}

- Evidence: {{finding_3_evidence}}
- Meaning: {{finding_3_meaning}}
- Limitation: {{finding_3_limitation}}

---

## 4. Interpretation

{{interpretation}}

---

## 5. Limitations

{{limitations}}

---

## 6. Next Steps

{{next_steps}}

---

## 7. Reproducibility

Generated files:

{{artifact_list}}

Package versions:

{{package_versions}}

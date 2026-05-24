# multi-source-playbook

Use this when a task has multiple files, multiple tables, or a SQLite database with more than one relevant table.

## 1. Build a data map first

Create a compact inventory before merging:

| field | required notes |
|---|---|
| source | file path or table name |
| shape | rows and columns |
| grain | one row means what |
| candidate keys | unique or nearly unique columns |
| time fields | event, snapshot, or update time |
| target availability | where the target or outcome lives |
| warnings | missingness, duplicates, odd ranges |

Do not join until the row grain is understood.

## 2. Join safety checks

For each join, record:

- left/right row counts before and after;
- join keys and key missing rates;
- key uniqueness on both sides;
- expected cardinality: one-to-one, one-to-many, many-to-one, or many-to-many;
- number and rate of unmatched rows;
- duplicated columns and how conflicts were resolved.

Many-to-many joins are suspect by default. Use them only when the duplicated grain is intended and explained.

## 3. Source traceability

Preserve enough source context to debug findings:

- keep original raw files untouched;
- write joined or cleaned data to `data/processed/` only when useful;
- add source columns only when they help interpret or audit the merge;
- list all inputs in `run_summary.json.input_files`;
- list generated joined datasets in `run_summary.json.generated_files`.

## 4. SQLite rules

When reading SQLite:

- inspect table names first;
- prefer the user-specified table when given;
- if no table is specified and there is one user table, read it;
- if multiple user tables exist, create a data map and decide whether to analyze one table or join;
- ignore SQLite internal tables such as `sqlite_sequence`.

## 5. When to split scripts

Stay with one script if the merge is simple and the analysis is one goal.

Split only when:

- sources have different cleaning logic;
- more than one independent target exists;
- one join path can fail without blocking other work;
- the script is heading beyond 400-500 lines.

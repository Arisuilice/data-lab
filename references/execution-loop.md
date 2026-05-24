# execution-loop

Use this when an analysis needs more than one run, a script fails, model performance is weak, or generated outputs need repair.

## 1. Minimal loop

```text
plan one run -> execute -> observe -> patch one issue -> rerun
```

Each loop should leave a short trace in `run_summary.json` or the report notes:

| item | meaning |
|---|---|
| action | what was run or changed |
| observation | metric, error, warning, or output produced |
| decision | continue, patch, stop, or ask |
| next_action | the one next move that matters |

## 2. Stop conditions

Stop iterating when:

- the user question is answered with evidence;
- a quality gate fails for a reason that needs user data or a decision;
- three targeted improvement rounds have not materially improved the result;
- runtime or dependency cost is no longer proportional to the task.

Do not continue just to make the process look complete.

## 3. Patch discipline

Patch one primary issue per loop:

- data read error;
- invalid join;
- leakage risk;
- weak split strategy;
- model underperformance;
- chart readability;
- report contradiction.

After patching, rerun the smallest command that proves the issue changed.

## 4. Reporting failed loops

If a loop cannot be fixed within scope, report:

- what was attempted;
- exact blocking error or weak metric;
- what is still reliable;
- what data, decision, or dependency is needed next.

Weak results are acceptable when reported honestly. Hidden weak results are not.

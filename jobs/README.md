# Monthly orchestration

One Databricks Job named `nyc_mobility_monthly` runs the four notebooks in order:

```text
prepare (00_prepare_batch) -> bronze (01_bronze) -> silver (02_silver) -> gold (03_gold)
```

- Compute: serverless (Databricks Free Edition). No cluster specification is stored in the JSON because the serverless compute is selected in the job UI.
- `run_if` is `ALL_SUCCESS` on every task, so a failed task stops the chain.
- `max_retries` is 0 on every task; a failed run is rerun by hand after the cause is fixed.
- `max_concurrent_runs` is 1, and there is no schedule: every run so far was started manually.
- All tasks receive the same `source_month` and `config_path` through job parameters, so a backfill or rerun uses the same workflow.

## `monthly_job.example.json`

This file is a tidied summary of the job settings exported from Databricks, with the user path replaced by `<email>`. It is not an Asset Bundle definition and not a byte-for-byte export, so do not expect `databricks jobs create --json @...` to work unchanged.

## Parameters

| Parameter | Meaning |
| --- | --- |
| `config_path` | Path to the batch configuration JSON in the workspace, for example `/Workspace/Users/<email>/nyc-mobility-lakehouse/config/batch.local.json`. Same name as the notebook widget. |
| `source_month` | Month to process, `YYYY-MM`. Same name as the notebook widget. |

The names are deliberately identical to the widget names: a job parameter with the same name as a widget overrides the widget value for that run.

`source_month` defaults to an empty string. A run started without parameters then fails immediately in `prepare` validation (`ValueError: source_month harus YYYY-MM, diterima: ''`, i.e. the month must be `YYYY-MM`) instead of silently processing a month whose file may not exist. It also means no month is baked into the committed JSON.

## How to recreate it

1. Import `notebooks/*.py` into the workspace under `nyc-mobility-lakehouse/notebooks/` (they use the Databricks source format).
2. Create a job with four notebook tasks, in the order above, and add `depends_on` so each task waits for the previous one.
3. Select serverless compute, set `max_concurrent_runs` to 1, set `max_retries` to 0 on every task, and leave the schedule off.
4. Add the two job parameters `config_path` and `source_month`, with `source_month` empty and `config_path` pointing at your own `batch.local.json`.
5. Run it once per month with `source_month` filled in, then rerun one month to check idempotency.

`config/batch.local.json` is git-ignored; see `config/README.md` for its fields.

## Failure behaviour

When a task fails, later tasks do not run and are shown as "Upstream failed". Delta commits are atomic per table, so a failure between tasks can leave the layers at different versions until the whole workflow is rerun for that month. Rerun the entire workflow with the same `source_month` after fixing the root cause; do not patch one layer by hand.

## Evidence

The four recorded runs (January, February, February rerun, failed `2024-03`) are described in `evidence/day6/06-rerun-comparison.md`. The job settings are visible in `evidence/day6/job_definition.png` (four chained tasks, `Maximum concurrent runs` 1, queue enabled) and `evidence/day6/runs_list.png` (no trigger configured, serverless compute). The Day 7 backfill reused the same job for seven months (2024-03 to 2024-09), one manual run per month; see `evidence/day7/07-backfill.md`.

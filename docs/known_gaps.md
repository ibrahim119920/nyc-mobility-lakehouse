# Known gaps and next steps

This file records what the project does **not** have, so nothing is missing by
accident. None of these gaps block the claims in the README or the evidence in
`evidence/`; they mark where the project would go next.

Status values: **open** (not started), **partial** (something exists but is
incomplete), **by design** (deliberately left out of the one-week scope).

| # | Area | Gap | Impact | What closing it would take | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Tests | The Spark transformations (Silver rules, Gold aggregation) are not covered by automated tests. Only `00_prepare_batch` runs in `pytest`, plus the repository contract. | A rule change can only be verified by a real Databricks run. | Add `delta-spark` with a JVM in CI (or Databricks Connect), load `tests/fixtures/yellow_trips_sample.csv` into a temporary table, and assert accepted/rejected counts and Gold reconciliation. | partial |
| 2 | Backfill | The `run_backfill` loop and the `workflow_check` notebook live only in the workspace. | The seven-month backfill cannot be reproduced from the repository. | Export both notebooks into `jobs/` (or `notebooks/`) with the user path parameterised, then link them from `evidence/day7/07-backfill.md`. | open |
| 3 | Deployment | The job is a tidied summary, not a deployable definition. | The job must be recreated by hand following `jobs/README.md`. | Add a Databricks Asset Bundle (`databricks.yml` + job resource) or a full `jobs get` export with the cluster/environment block. | open |
| 4 | Zone names | Zones stay numeric IDs; there is no lookup join. | "Top zone" results cannot be named. | Add `taxi_zone_lookup.csv` as a small dimension table and a `LEFT JOIN` in the analysis queries; keep the numeric ID as the key. | open |
| 5 | Coverage | Only 2024-01 to 2024-09 are loaded. | No full-year claim; seasonality is limited to nine months. | Download October-December, run the same job three times, then extend `evidence/day7/07-analysis.md`. | open |
| 6 | Quality rules | For 2024-03 to 2024-09, null `PULocationID` and negative `trip_distance` were not measured. | The per-rule rejection breakdown is unknown for those months. | Re-run the preflight with the full six-rule set and record the two missing counters. | open |
| 7 | Rejected rows | Rejected rows are counted and dropped, not stored. | Rejected records cannot be audited or reprocessed. | Write rejects to `silver_yellow_trips_rejected` (or a log table) with the failing rule name, partitioned by `source_month`. | open |
| 8 | Duration | No cap on `trip_duration_min`; maximum is 9,767.5 minutes (April 2024) and 796-1,132 trips per month have zero duration. | `avg_trip_duration_min` in Gold is skewed by the tail. | Choose a threshold (fixed or percentile), add a Silver rule, and reprocess every loaded month so Gold stays reproducible. | open |
| 9 | Money | Negative monetary values are kept; there is no refund rule. | Totals include refunds and reversals. | Define a refund policy, then add a rule or a separate flag column. | open |
| 10 | Failure recovery | A failure between layers leaves the tables at different versions until the month is rerun by hand. | A partially written month can be consumed by mistake. | Add a `_pipeline_status` table per month, or read Gold only after a successful run; long term, one transaction per month. | by design |
| 11 | Concurrency | Single writer only (`max_concurrent_runs = 1`); parallel runs were never tested. | Safe for the current workload, but no multi-writer support. | Test concurrent runs against separate months, then decide whether a lock or idempotent merge is needed. | by design |
| 12 | Evidence | Six outputs were never captured: `DESCRIBE DETAIL` after table creation, the `0/0/0` count, the Bronze checksum query, Silver v9 history, Gold v0-v4 history, and the Day 6 `snap_a`/`snap_b` comparison. Day 1 has no evidence folder. | Those steps are described but not pictured. | Re-run the queries on a fresh workspace or accept the notes in `evidence/README.md`. | by design |
| 13 | Provenance | Analysis CSVs contain no run timestamp or query ID. | Results cannot be tied to one run without the file modification time. | Add `run_id` and `exported_at` columns to the export step (or run the queries from a job that stamps them). | open |
| 14 | Automation | CI runs tests and lint only; there is no schedule or deployment pipeline. | Every run is started by hand. | Add a schedule or a `databricks bundle deploy` workflow once the job definition is deployable (item 3). | by design |

## Intentionally out of scope

Streaming, dashboards, a zone-name map, and multi-dataset orchestration were
never part of the one-week scope; see `docs/week_plan.md` for the original
priorities.

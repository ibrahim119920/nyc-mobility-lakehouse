# Day 6 Evidence: Workflow Runs and the February Rerun

Date: 2026-11-05
Environment: Databricks Free Edition (serverless), job `nyc_mobility_monthly` (four chained tasks: prepare, bronze, silver, gold)
Time zones: `DESCRIBE HISTORY` timestamps and the `last_write` column are **UTC**; Databricks screen timestamps (Runs tab, run detail, query refresh) are **WIB (UTC+7)**.

The test ran on tables that were already populated with January and February during Day 3-5 development, not on empty tables.

## 1. Runs

From `runs_list.png` (Runs tab) and `run_january_detail.png`:

| Run | Parameter `source_month` | Start (WIB) | Duration | Result |
| --- | --- | --- | --- | --- |
| 1 | 2024-01 | 11:38, ended 11:40 | 1m 38s (run detail; the Runs list shows 1m 39s) | succeeded: prepare 44s, bronze 19s, silver 22s, gold 10s |
| 2 | 2024-02 | 11:51 | 1m 40s | all tasks succeeded (prepare 43s, bronze 19s, silver 23s, gold 10s) |
| 3 (rerun) | 2024-02 | 12:02 | 1m 10s | all tasks succeeded (prepare 21s, bronze 14s, silver 20s, gold 10s) |
| 4 | 2024-03 | 12:05 | 24s | prepare failed after 22s; bronze, silver, gold: "Upstream failed" (0s) |

The Runs tab starts are 11:38, 11:51, 12:02 and 12:05. The earlier working notes recorded 1m 39s, 1m 9s and 23s for runs 2-4 and no duration for the January run; the Runs tab and run detail show 1m 40s, 1m 10s and 24s (and 1m 38s for January). The difference is one second per run and comes from which page the number was read on. The task durations (43s, 19s, ...) are from the run graph and do not add up exactly to the wall-clock duration because of task start overhead.

The January run is also confirmed by the January `last_write` values in Bronze and Silver (2026-11-05 04:39:40 and 04:40:04 UTC, i.e. 11:39:40 and 11:40:04 WIB).

## 2. February rerun (snap_a vs snap_b)

Delta versions: Bronze 7 -> 8, Silver 11 -> 12, Gold 6 -> 7 (one new version per table, from one rerun).

| Layer | Month | Business columns | `last_write` changed |
| --- | --- | --- | --- |
| Bronze | 2024-01 | IDENTICAL | False |
| Bronze | 2024-02 | IDENTICAL | True |
| Silver | 2024-01 | IDENTICAL | False |
| Silver | 2024-02 | IDENTICAL | True |
| Gold | 2024-01 | IDENTICAL | False (Gold has no write-timestamp column) |
| Gold | 2024-02 | IDENTICAL | False (Gold has no write-timestamp column) |

Compared values: `n`, `SUM(total_amount)`, `SUM(trip_distance)`, and the duration aggregate available in each layer (Silver: `SUM(trip_duration_min)`; Gold: `SUM(avg_trip_duration_min)`, the only duration column Gold has). `last_write` for February: Bronze 04:52:33 -> 05:03:04 UTC, Silver 04:52:58 -> 05:03:25 UTC. January did not change.

Gold has no write-timestamp column, so its `last_write` comparison is always False and is not proof of anything. The Gold proof is the Delta version moving from 6 to 7 plus identical business columns.

`silver_rerun_v8_v9.png` in this folder is **not** the Day 6 cross-layer comparison: it is the earlier Silver-only rerun test from 2026-11-04 (version 8 -> 9), printing "Versi terakhir sebelum rerun: 8" and then `2024-01 IDENTIK` / `2024-02 IDENTIK`. There is no screenshot of the Day 6 Bronze/Silver/Gold snap_a vs snap_b query. The same cross-layer comparison for January and February — business columns IDENTIK and the `last_write` flags — is shown for the Day 7 before/after snapshot in `evidence/day7/snapshot_after_backfill.png`.

## 3. Failed input (2024-03)

From `failed_run_detail.png`:

- Task `prepare` failed after 22s with `FileNotFoundError: Input tidak ditemukan: /Volumes/workspace/nyc_mobility/raw/yellow/2024-03/yellow_tripdata_2024-03.parquet` (input not found).
- Tasks bronze, silver, gold did not run ("Upstream failed", 0s).
- snap_c ("after failed input") compared with snap_b: everything IDENTICAL, `last_write` unchanged, Delta versions stayed 8 / 12 / 7.
- One successful run adds one version per table, so an unchanged version number shows that the failed run wrote nothing.

## 4. Final counts per month

From `final_counts.png` (`SELECT ... UNION ALL` over the three layers), refreshed 2026-11-05 12:16 WIB, after the failed run. See `02-monthly-counts.csv`.

| Layer | 2024-01 | 2024-02 |
| --- | --- | --- |
| Bronze rows | 2,964,624 | 3,007,526 |
| Silver rows | 2,964,550 | 3,007,504 |
| Gold `SUM(trip_count)` | 2,964,550 | 3,007,504 |

These January and February numbers were unchanged by the Day 7 backfill: the backfill compared a "before" and "after" snapshot of both months and reported the business columns identical and `last_write` unchanged for all three layers. The `2024-03` file that failed here was uploaded later, and the same month succeeded during that backfill; see `evidence/day7/07-backfill.md`.

## 5. Screenshots

| File | Content |
| --- | --- |
| `runs_list.png` | Runs tab: four runs with start time, duration, status; failed run at 12:05; compute serverless; no trigger configured |
| `run_january_detail.png` | January run: 11:38-11:40, 1m 38s, succeeded; task graph with 44s/19s/22s/10s; job parameters |
| `failed_run_detail.png` | `2024-03` prepare task: `FileNotFoundError`, failed after 22s, resolved parameters |
| `final_counts.png` | Final counts query, 6 rows, refreshed 12:16 WIB |
| `job_definition.png` | Tasks tab: four chained tasks, `Maximum concurrent runs` 1, queue enabled |
| `silver_rerun_v8_v9.png` | Silver-only rerun test from 2026-11-04 (v8 -> v9), snapshot A/B values |

## 6. Limits of this evidence

- The test ran on tables already populated by the Day 3-5 development runs, not from an empty catalog. It proves idempotency of a rerun, not a first-time load from scratch in one clean run.
- Bronze, Silver, and Gold were written several times during development. The Silver idempotency proof is version 9; earlier versions (v1-v8) are development runs.
- The January run was not photographed while it ran; `run_january_detail.png` and `runs_list.png` were captured later from the Runs tab, so they show the stored record, not a live run.
- Gold has no write-timestamp column; the Gold proof is the Delta version, not a timestamp comparison.
- Delta commits are atomic per table, not across the three tables. A failure between tasks can leave the layers at different versions until the workflow is rerun for that month.
- There is a single writer. Parallel runs were not tested; the job is configured with `max_concurrent_runs = 1` and no schedule.
- "Identical" above means the listed business columns were compared; it is not a full-table checksum of every column.
- The Day 6 comparison table in section 2 has no screenshot of its own; only the run-level screenshots and the earlier Silver test were captured.

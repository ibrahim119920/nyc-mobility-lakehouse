# Day 7 Evidence: Backfill March-September 2024

Date: 2026-11-06, around 18:55-21:37 WIB
Environment: Databricks Free Edition (serverless), job `nyc_mobility_monthly` (same four chained tasks as Day 6), tables in `workspace.nyc_mobility`
Time zones: Delta `last_write` and the times printed by the backfill script are **UTC** (12:00:49 UTC = 19:00:49 WIB); the Runs tab and the notebook cell timers are **WIB (UTC+7)**.

## 1. What was done

Seven new months (2024-03 to 2024-09) were loaded by running the existing job once per month with `source_month` set to that month. The Runs tab shows the same `nyc_mobility_monthly` job as Day 6; no separate backfill notebook was used to write the tables. The backfill script only calls the job in a loop and waits for each run to finish.

Before starting, a preflight ran per month and a snapshot of the current tables was taken. After the last run, the same snapshot was taken again and compared. The script (`run_backfill`) and the preflight/snapshot notebook (`workflow_check`) live in the workspace but are **not** in this repository. Their outputs are captured in the screenshots in this folder; the notebook source itself was not exported, so it is not available here.

This is a backfill of new partitions on tables that already held January and February; it is not a load into empty tables.

## 2. Preflight per month

From `preflight_2024_03_09.png`, `workflow_check` cell 7. The preflight compared the source schema to the Bronze schema and counted rows and two failure types:

| source_month | Rows | Pickup outside the month | Dropoff before pickup | Schema |
| --- | --- | --- | --- | --- |
| 2024-03 | 3,582,628 | 23 | 117 | same (`SAMA`) |
| 2024-04 | 3,514,289 | 9 | 70 | same |
| 2024-05 | 3,723,833 | 33 | 42 | same |
| 2024-06 | 3,539,193 | 51 | 8 | same |
| 2024-07 | 3,076,903 | 47 | 5 | same |
| 2024-08 | 2,979,183 | 51 | 9 | same |
| 2024-09 | 3,633,030 | 49 | 45 | same |

The new months have the same schema as January/February. The two failure types add up exactly to the rejected rows reported later (section 5), which also means no row fails both rules in these months.

## 3. Runs

From `backfill_loop_output.png` (the loop output) and `runs_list_backfill.png` (Runs tab):

| source_month | Start (UTC, printed) | Start (WIB) | Script duration | Runs tab duration | Run ID | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-03 | 12:00:49 | 19:00 | 103s | 1m 38s | 622485813677001 | Succeeded |
| 2024-04 | 12:02:32 | 19:02 | 72s | 1m 6s | 713301150003862 | Succeeded |
| 2024-05 | 12:03:44 | 19:03 | 71s | 1m 7s | 811552771269467 | Succeeded |
| 2024-06 | 12:04:55 | 19:04 | 73s | 1m 6s | 938253796943325 | Succeeded |
| 2024-07 | 12:06:08 | 19:06 | 73s | 1m 5s | 977394806280712 | Succeeded |
| 2024-08 | 12:07:22 | 19:07 | 675s | 11m 6s | 927522183408919 | Succeeded |
| 2024-09 | 12:18:36 | 19:18 | 73s | 1m 7s | 381190790648339 | Succeeded |

- All seven runs succeeded; the loop cell reports a total of 19 minutes.
- The script duration is a few seconds longer than the Runs tab duration because it includes starting the run and polling for the result.
- The start times printed by the loop are UTC: 12:00:49 UTC is 19:00:49 WIB, which is the 07:00 PM run in the Runs tab.
- 2024-08 took 675s (11m 6s) instead of about 70s. It still succeeded and wrote the expected rows; the cause was not investigated. This is a known anomaly, not a failure.

## 4. Delta versions

From the snapshot output in `preflight_2024_03_09.png` and `snapshot_after_backfill.png`:

| Point in time | Bronze | Silver | Gold |
| --- | --- | --- | --- |
| Before the backfill | 8 | 12 | 7 |
| After the backfill | 15 | 19 | 14 |

Each layer gained exactly seven versions for seven months, i.e. one write per month per table, consistent with the `replaceWhere` design.

## 5. Post-backfill counts and reconciliation

From `reconciliation_nine_months.png` (query joining Bronze, Silver, and Gold by `source_month`, refreshed 21:37 WIB):

| source_month | Bronze rows | Rejected | Silver rows | Gold `SUM(trip_count)` | Difference | Gold rows |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-01 | 2,964,624 | 74 | 2,964,550 | 2,964,550 | 0 | 6,949 |
| 2024-02 | 3,007,526 | 22 | 3,007,504 | 3,007,504 | 0 | 6,499 |
| 2024-03 | 3,582,628 | 140 | 3,582,488 | 3,582,488 | 0 | 7,180 |
| 2024-04 | 3,514,289 | 79 | 3,514,210 | 3,514,210 | 0 | 6,943 |
| 2024-05 | 3,723,833 | 75 | 3,723,758 | 3,723,758 | 0 | 7,260 |
| 2024-06 | 3,539,193 | 59 | 3,539,134 | 3,539,134 | 0 | 6,993 |
| 2024-07 | 3,076,903 | 52 | 3,076,851 | 3,076,851 | 0 | 7,191 |
| 2024-08 | 2,979,183 | 60 | 2,979,123 | 2,979,123 | 0 | 7,267 |
| 2024-09 | 3,633,030 | 94 | 3,632,936 | 3,632,936 | 0 | 7,097 |

Checks:

- `Bronze - rejected = Silver` for every month: 3,582,628 - 140 = 3,582,488, 3,514,289 - 79 = 3,514,210, 3,723,833 - 75 = 3,723,758, 3,539,193 - 59 = 3,539,134, 3,076,903 - 52 = 3,076,851, 2,979,183 - 60 = 2,979,123, 3,633,030 - 94 = 3,632,936.
- Rejected rows equal the preflight failures: 23 + 117 = 140, 9 + 70 = 79, 33 + 42 = 75, 51 + 8 = 59, 47 + 5 = 52, 51 + 9 = 60, 49 + 45 = 94.
- `Gold SUM(trip_count) - Silver = 0` for all nine months.
- `min_pickup`/`max_pickup` fall inside each month's own range.

## 6. Checksums per month after the backfill

From `snapshot_after_backfill.png`:

| source_month | Bronze `SUM(total_amount)` | Bronze `SUM(trip_distance)` | Gold `SUM(total_amount)` | Gold `SUM(total_distance)` |
| --- | --- | --- | --- | --- |
| 2024-03 | 97,162,913.97 | 16,184,205.17 | 97,158,149.49 | 16,183,378.37 |
| 2024-04 | 96,619,892.35 | 18,568,977.97 | 96,616,785.96 | 18,568,413.32 |
| 2024-05 | 105,662,803.2 | 19,985,997.28 | 105,659,924.38 | 19,985,487.33 |
| 2024-06 | 98,854,638.37 | 18,481,638.7 | 98,853,108.04 | 18,481,464.67 |
| 2024-07 | 86,418,496.54 | 15,728,474.14 | 86,416,719.61 | 15,728,217.09 |
| 2024-08 | 84,225,045.0 | 14,731,655.02 | 84,223,219.53 | 14,731,421.46 |
| 2024-09 | 103,683,398.86 | 20,858,929.41 | 103,680,692.85 | 20,858,459.18 |

Gold totals are lower than Bronze totals because Gold is built from Silver, which dropped the rejected rows. The same holds for 2024-05: Bronze `SUM(total_amount)` is 105,662,803.2 and Gold is 105,659,924.38, so Gold is lower by 2,878.82. There is no month where Gold is higher than Bronze in this snapshot.

## 7. January and February unchanged

From the `compare(snap_before_bf, snap_after_bf)` output in `snapshot_after_backfill.png`:

| Layer | 2024-01 | 2024-02 |
| --- | --- | --- |
| Bronze | business IDENTICAL, `last_write` changed: False | business IDENTICAL, `last_write` changed: False |
| Silver | business IDENTICAL, `last_write` changed: False | business IDENTICAL, `last_write` changed: False |
| Gold | business IDENTICAL, `last_write` changed: False | business IDENTICAL, `last_write` changed: False |

The January/February values in the "before" snapshot also match the Day 6 final numbers (Bronze 2,964,624 / 3,007,526; Silver 2,964,550 / 3,007,504; Gold 6,949 / 6,499), and the stored `last_write` values are still the Day 6 ones (2026-11-05 04:39:40, 04:40:04, 05:03:04, 05:03:25 UTC).

## 8. Related screenshots

| File | Content | Time (WIB) |
| --- | --- | --- |
| `preflight_2024_03_09.png` | Preflight per month (rows, outside-month pickups, dropoff-before-pickup, schema) and the "before" snapshot with Delta versions 8/12/7 | 18:55 |
| `backfill_loop_output.png` | Backfill loop output: start time, run ID, status, duration for the seven runs | 19:00-19:19 |
| `snapshot_after_backfill.png` | "After" snapshot with versions 15/19/14, per-month values for 2024-03 to 2024-09, and the before/after comparison for January/February | 21:27 |
| `runs_list_backfill.png` | Runs tab for 2026-11-06: seven successful runs, 1m 5s to 11m 6s | 21:29 |
| `reconciliation_nine_months.png` | Reconciliation query across Bronze, Silver, and Gold for all nine months | 21:37 |

The twelve descriptive queries run on these nine months are documented separately in `07-analysis.md`, with one CSV export per query.

## 9. Limits of this evidence

- The backfill ran on tables that already contained January and February, not on an empty catalog.
- Only rows, outside-month pickups, dropoff-before-pickup, and schema equality were checked before the run. Null `PULocationID` and negative distance were **not** measured for 2024-03 to 2024-09, so it is not known whether those rules rejected anything in these months. The Silver per-rule counts for these months are not stored.
- The preflight reads the source file directly; it does not compute a checksum of the file, so the input is identified by month and row count only.
- The 2024-08 run was about ten times slower than the others (11m 6s); no cause was investigated.
- Delta commits are atomic per table, not across the three tables, and only one job runs at a time.
- Zones are still IDs; there is no zone-name lookup, no deduplication (no unique trip ID), and negative money values are kept.
- The backfill and preflight scripts are not in the repository, so the loop and the snapshot function cannot be reviewed from the repo alone.

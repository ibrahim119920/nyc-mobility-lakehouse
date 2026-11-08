# Portfolio evidence

This folder holds the evidence that was kept after the pipeline was actually run in Databricks. Every file listed here exists in this folder; nothing is planned or simulated.

Some screenshots contain Indonesian text: the notebook error messages, the widget labels, and parts of the Databricks UI are in Indonesian and were not translated. Screenshots taken before the repository was translated also show the old Indonesian code comments and print output; the logic shown matches the current code, only the comment language differs.

## Index

| Folder | Contents | Claim proven |
| --- | --- | --- |
| `day2/` | `00-day2-setup.md`, `prepare_batch_01.png` ... `prepare_batch_05.png`, `row_count.png` | The three Delta tables exist, empty, partitioned by `source_month`; `00_prepare_batch` rejects a malformed month, an impossible month, and a month with no file, all before writing. |
| `day3/` | `03-bronze.md`, `bronze_row_count_before_rerun.png`, `bronze_history_v0_v4.png`, `bronze_history_v0_v5.png`, `bronze_row_count_after_rerun.png` | Bronze holds the exact source row count for January and February; Delta history v0-v5 shows that each write replaced only the active month's partition; the Bronze checksum is unchanged by the February rerun. |
| `day4/` | `04-silver.md`, `04-quality-results.csv`, `silver_output_01.png`, `silver_output_02.png`, `silver_duration_check.png`, `silver_history.png` | Silver accepted 2,964,550 / 3,007,504 rows and rejected 74 / 22; all rejections come from `dropoff_not_before_pickup` and `pickup_in_source_month`; `input = accepted + rejected`. |
| `day5/` | `05-gold.md`, `gold_output_01.png`, `gold_output_02.png`, `gold_histogram_top_zones.png`, `analysis_daily_trend.png`, `gold_reconciliation.png` | Gold has one row per `source_month + pickup_date + pickup_location_id` (6,949 / 6,499 rows), `SUM(trip_count)` equals the Silver row count with difference 0, and the February rerun did not change either month. |
| `day6/` | `06-rerun-comparison.md`, `02-monthly-counts.csv`, `runs_list.png`, `run_january_detail.png`, `failed_run_detail.png`, `final_counts.png`, `job_definition.png`, `silver_rerun_v8_v9.png` | The chained Job ran four times (January, February, February rerun, failed 2024-03); the February rerun left all business columns identical and January untouched; the failed input run wrote nothing (Delta versions unchanged). |
| `day7/` | `07-backfill.md`, `07-analysis.md`, `preflight_2024_03_09.png`, `backfill_loop_output.png`, `snapshot_after_backfill.png`, `runs_list_backfill.png`, `reconciliation_nine_months.png`, `analysis_01` ... `analysis_12` CSV files | Seven more months (2024-03 to 2024-09) were loaded through the same job, one run per month; all seven runs succeeded; Delta versions moved 8/12/7 -> 15/19/14 (one per month per table); January and February were verified unchanged. The 12 analysis queries were then run for all nine months; every result set is exported as a CSV. |
| (root) | `README.md` | This index. |

Day 1 of the plan (workspace setup and monthly file download) produced no table or query output, so it has no evidence folder; the reproducible parts are recorded in `data/README.md` and `docs/schema_notes.md`.

Raw exports, full logs, and unfiltered screenshots go in `evidence/raw/`, which `.gitignore` excludes.

## Honesty notes

(a) The Day 6 test ran on tables that were already populated during Day 3-5 development, not on empty tables.
(b) Bronze, Silver, and Gold were run several times during development. Silver versions v1-v8 are development runs; the Silver idempotency proof is v9.
(c) The Day 6 January run was not photographed while it ran; its run detail and the runs list were captured later from the Runs tab (`day6/run_january_detail.png`, `day6/runs_list.png`).
(d) Zones are still numeric IDs. There is no zone-name lookup yet, so no zone can be named in the analysis.
(e) The source has no unique trip ID, so no deduplication is done; two identical source rows stay two rows.
(f) Delta is atomic per table, not across the three tables. A failure between tasks can leave Bronze, Silver, and Gold at different versions until the month is rerun.
(g) There is a single writer. Parallel runs were not tested; the job is configured with `max_concurrent_runs = 1` and has no schedule.
(h) Negative money values are kept. Refund rules and zone-ID validation do not exist yet, and trip duration is not capped.
(i) The Day 7 backfill ran on tables that already held January and February, not on an empty catalog. For 2024-03 to 2024-09 the preflight checked only row counts, outside-month pickups, dropoff-before-pickup, and schema equality; null `PULocationID` and negative `trip_distance` were not measured for those months, so only the two preflight failure counts are available and the other two rules were not counted.
(j) The Day 7 loop (`run_backfill`) and the preflight/snapshot notebook (`workflow_check`) exist in the Databricks workspace but are not in this repository. The 2024-08 run took 11m 6s versus about 1m for the other months and the cause was not investigated.
(k) The analysis result files in `day7/` are CSV exports, not query definitions: they contain no run timestamp or query ID. The query text is in `sql/02_analysis.sql`, and the exported numbers were not re-run by an automated test. Coverage stops at September 2024, so no full-year claim is made.
(l) Six outputs were described but never captured: `DESCRIBE DETAIL` right after table creation, the `0/0/0` count after the validation cases, the Bronze checksum query, a `DESCRIBE HISTORY` that includes Silver v9, the Gold v0-v4 history rows, and the Day 6 `snap_a`/`snap_b` comparison. The day files say so where it matters; `docs/known_gaps.md` tracks it as item 12.

## Conventions used in these files

- `DESCRIBE HISTORY` timestamps and `last_write` are **UTC**.
- Databricks screen timestamps (Runs tab, query refresh time) are **WIB (UTC+7)**.
- CSV result files in `day7/` contain no timestamps; their file modification times are **WIB (UTC+7)**.
- Business-column comparisons ignore load metadata such as `ingested_at`, `processed_at`, and `source_file`.

The screenshots were reviewed by hand before publishing; the table below records what was covered and what was left as is.

## Redaction status

The account email has been covered with a black box in the three images that showed it, and the edit was checked by eye afterwards:

- `day4/silver_history.png` — `userName` shows only `@gmail.com...`; the `userId` tail is covered too.
- `day6/run_january_detail.png` — the user segment of `config_path` is covered; only `/Workspace/Users/` and the trailing `.../nyc-mobility-` remain.
- `day6/failed_run_detail.png` — `Run as` shows only `@gmail.com`, and the user segment of `config_path` is covered.

The images below still show a truncated workspace user path or a truncated account name. This was reviewed and accepted: the visible fragments are cut off and do not contain the full address, so no further editing is planned.

| File | What is visible | Where |
| --- | --- | --- |
| `day2/prepare_batch_01.png` ... `prepare_batch_05.png` | truncated workspace user path | `config_path` widget |
| `day4/silver_output_01.png`, `day4/silver_output_02.png` | truncated workspace user path | `config_path` widget |
| `day5/gold_output_01.png`, `gold_output_02.png` | truncated workspace user path | `config_path` widget |
| `day6/job_definition.png` | truncated account name | `Permissions` panel, owner row |
| `day7/backfill_loop_output.png` | truncated workspace user path | `config_path` widget |
| `day7/runs_list_backfill.png` | truncated account name | `Run as` column |

Apart from the three covered images above and the truncated fragments listed in the table, no other screenshot shows the email or the user path.

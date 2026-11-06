# Day 5 Evidence: Gold

Date: 2026-11-04
Environment: Databricks Free Edition (serverless), `workspace.nyc_mobility.gold_daily_pickup_zone`
Time zones: `DESCRIBE HISTORY` timestamps are **UTC**; Databricks screen timestamps (query refresh time, notebook tab name) are **WIB (UTC+7)**. Screenshots were taken around 11:27-11:34 WIB.

## 1. `03_gold` notebook output

From `gold_output_01.png` (2024-01) and `gold_output_02.png` (2024-02):

| Metric | 2024-01 | 2024-02 |
| --- | --- | --- |
| silver_rows | 2,964,550 | 3,007,504 |
| gold_rows | 6,949 | 6,499 |
| sum_trip_count | 2,964,550 | 3,007,504 |

The notebook stops the run (`RuntimeError`) if the Gold `SUM(trip_count)` differs from the number of Silver rows. Both runs finished without errors.

## 2. Gold contents verification

| source_month | gold_rows | sum_trip_count | min_date | max_date | zones |
| --- | --- | --- | --- | --- | --- |
| 2024-01 | 6,949 | 2,964,550 | 2024-01-01 | 2024-01-31 | 260 |
| 2024-02 | 6,499 | 3,007,504 | 2024-02-01 | 2024-02-29 | 254 |

- Dates fall within their own month.
- `duplicate_grain = 0`: the grain `source_month + pickup_date + pickup_location_id` is unique.

## 3. Gold reconciliation against Silver (separate query)

From `gold_reconciliation.png`:

| source_month | silver_rows | gold_trip_count | difference |
| --- | --- | --- | --- |
| 2024-01 | 2,964,550 | 2,964,550 | 0 |
| 2024-02 | 3,007,504 | 3,007,504 | 0 |

## 4. Gold checksums (SQL query, captured after version 4)

| source_month | gold_rows | sum_trip_count | sum_distance | sum_fare | sum_total | sum_duration |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-01 | 6,949 | 2,964,550 | 10,826,845.05 | 53,880,103.2 | 79,454,065.5 | 46,286,364.08 |
| 2024-02 | 6,499 | 3,007,504 | 11,611,564.98 | 54,277,288.11 | 80,073,049.72 | 48,067,561.23 |

`sum_total`, `sum_distance`, and `sum_duration` match the Silver checksums. The Silver side of that comparison is the rerun-test output in `evidence/day6/silver_rerun_v8_v9.png`:

| source_month | n | sum_total | sum_distance | sum_duration |
| --- | --- | --- | --- | --- |
| 2024-01 | 2,964,550 | 7.94540655E7 (79,454,065.5) | 1.082684505E7 (10,826,845.05) | 4.628636408E7 (46,286,364.08) |
| 2024-02 | 3,007,504 | 8.007304972E7 (80,073,049.72) | 1.161156498E7 (11,611,564.98) | 4.806756123E7 (48,067,561.23) |

## 5. Rerun evidence (idempotency)

Snapshot A was taken before the February rerun, snapshot B after it. Comparison over `gold_rows`, `sum_trip_count`, `sum_distance`, `sum_fare`, `sum_total`, and `sum_duration`: 2024-01 IDENTICAL, 2024-02 IDENTICAL.

The February rerun was run twice (versions 3 and 4, four seconds apart); snapshots A and B bracket both.

## 6. Gold Delta history (UTC)

| Version | Time (UTC) | Time (WIB) | Predicate | Rows written | Files removed | Files added |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 2026-10-31 04:52:03 | 11:52:03 | - | - | - | - |
| 1 | 2026-11-04 04:27:47 | 11:27:47 | `'2024-01'` | 6,949 | 0 | 1 |
| 2 | 2026-11-04 04:28:10 | 11:28:10 | `'2024-02'` | 6,499 | 0 | 1 |
| 3 | 2026-11-04 04:31:10 | 11:31:10 | `'2024-02'` | 6,499 | 1 | 1 |
| 4 | 2026-11-04 04:31:14 | 11:31:14 | `'2024-02'` | 6,499 | 1 | 1 |

- Version 0: `CREATE TABLE`. Versions 1 through 4: `WRITE` overwrite with a per-month predicate. No overwrite without a predicate.
- The January partition does not appear again after version 1, so it was untouched by the February rerun.
- Versions after 4 were created during Day 6 (Gold 6 -> 7 on the February rerun; see `evidence/day6/06-rerun-comparison.md`) and Day 7 (Gold 7 -> 14 across the seven backfilled months; see `evidence/day7/07-backfill.md`). This table is a Day 5 snapshot and has no screenshot of its own. The Day 7 snapshot (`evidence/day7/snapshot_after_backfill.png`) records Gold at version 14 with per-month values; it does not show the v0-v4 history rows.

## 7. Analysis results (`sql/02_analysis.sql`)

The file now holds 12 queries (monthly summary, month-over-month change, daily trend, busiest/quietest day, weekday pattern, top zones per month, top zones overall, zone concentration, hourly profile, payment types, duration profile, reconciliation). The screenshots in this folder were taken on 2026-11-04, when the file still held only three queries, so they map to the current numbering as follows:

- `gold_histogram_top_zones.png` -> query 6 (top ten pickup zones per month). January: zones 132 (145,240), 161 (143,469), 237 (142,707). February: zones 161 (147,086), 237 (140,800), 236 (134,000). Zones are still IDs.
- `analysis_daily_trend.png` -> query 3 (daily trend), 60 rows (31 January + 29 February). Example: 2024-01-01 = 81,011 trips, revenue 2,442,761.74.
- `gold_reconciliation.png` -> query 12 (reconciliation; see section 3).

The same queries were rerun for all nine months after the Day 7 backfill; those results are in `evidence/day7/07-analysis.md` and the CSV files next to it. These results are descriptive. There is no business interpretation without a zone-name lookup.

## 8. Screenshots

| File | Content | Time (WIB) |
| --- | --- | --- |
| `gold_output_01.png` | `03_gold` output 2024-01: silver_rows 2,964,550, gold_rows 6,949 | 11:27 |
| `gold_output_02.png` | `03_gold` output 2024-02: silver_rows 3,007,504, gold_rows 6,499 | 11:28 |
| `gold_histogram_top_zones.png` | Top-10 pickup zones per month (20 rows) | 11:33 |
| `analysis_daily_trend.png` | Daily trips and revenue (60 rows) | 11:34 |
| `gold_reconciliation.png` | Silver vs `SUM(trip_count)` Gold, difference 0 / 0 | 11:34 |

The screenshots were taken before the SQL comments were translated into English, so the visible comments are still Indonesian. They show the three-query version of the file; those three queries are queries 6, 3, and 12 in the current twelve-query file.

## 9. Limits of this evidence

- Zones are IDs only; there is no zone-name lookup, so a "top zone" cannot be named.
- Gold has no write-timestamp column, so a rerun can only be proven through the Delta version and the business columns.
- Gold is aggregated; it cannot be used to inspect individual trips or to find the 74 / 22 rejected rows.
- There is no chart image in the repo; `analysis_daily_trend.png` is a table view of the daily query.

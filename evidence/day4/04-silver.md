# Day 4 Evidence: Silver Quality Rules

Date: 2026-11-04
Environment: Databricks Free Edition (serverless), `workspace.nyc_mobility.silver_yellow_trips`, built from `bronze_yellow_trips` for one `source_month` at a time
Time zones: `DESCRIBE HISTORY` timestamps are **UTC**; Databricks screen timestamps (query refresh time, notebook tab name) are **WIB (UTC+7)**. Screenshots were taken around 10:57-11:02 WIB.

## 1. Input, accepted, and rejected rows

Sources: `silver_output_01.png` (2024-01) and `silver_output_02.png` (2024-02) for the notebook output, `04-quality-results.csv` for the same numbers in a machine-readable form.

| source_month | Input | Accepted | Rejected |
| --- | --- | --- | --- |
| 2024-01 | 2,964,624 | 2,964,550 | 74 |
| 2024-02 | 3,007,526 | 3,007,504 | 22 |

`input = accepted + rejected` holds for both months.

## 2. Failures per rule

| Rule | 2024-01 | 2024-02 |
| --- | --- | --- |
| `pickup_not_null` | 0 | 0 |
| `dropoff_not_null` | 0 | 0 |
| `pu_location_not_null` | 0 | 0 |
| `distance_non_negative` | 0 | 0 |
| `dropoff_not_before_pickup` | 56 | 7 |
| `pickup_in_source_month` | 18 | 15 |

- No row fails two rules at once, so the rejected count is exactly the sum of the per-rule failures (74 = 56 + 18, 22 = 7 + 15).
- The `pickup_in_source_month` failures match the pickups outside the file month counted in Bronze (18 and 15).
- No source row has a null `PULocationID`, a null pickup/dropoff timestamp, or a negative `trip_distance` in these two months. The rules are still defined, but they do not remove any rows here.

## 3. Derived columns

Silver keeps `VendorID`, both timestamps as `pickup_ts`/`dropoff_ts`, `passenger_count`, `trip_distance`, `PULocationID` as `pickup_location_id`, `DOLocationID` as `dropoff_location_id`, `payment_type`, `fare_amount`, `tip_amount`, `total_amount`, plus:
- `pickup_date` = date of `pickup_ts`.
- `trip_duration_min` = `(dropoff_ts - pickup_ts)` in minutes, as a double.
- `source_month` and `processed_at`.

## 4. Long-duration finding

From `silver_duration_check.png`:

| source_month | min `trip_duration_min` | max `trip_duration_min` |
| --- | --- | --- |
| 2024-01 | 0 | 9,455.4 |
| 2024-02 | 0 | 5,671.98 |

The initial rules do not cap trip duration, so these rows are kept. 9,455.4 minutes is about 6.6 days for a single taxi trip, which is almost certainly a meter or timestamp error, but there is no agreed threshold yet, so no duration rule was added. This is a known limitation, not a bug that was fixed. The minimum of 0 minutes is also not filtered. The nine-month duration profile is in `evidence/day7/07-analysis.md`.

## 5. Rerun behaviour

- Silver is written with `mode("overwrite")` + `replaceWhere "source_month = 'YYYY-MM'"`, so a rerun replaces exactly one month's partition.
- The rerun test printed "Versi terakhir sebelum rerun: 8" (latest version before the rerun), took snapshot A, reran, took snapshot B, and printed `2024-01 IDENTIK` and `2024-02 IDENTIK`. The compared values were `n`, `SUM(total_amount)`, `SUM(trip_distance)`, and `SUM(trip_duration_min)`. The output is `evidence/day6/silver_rerun_v8_v9.png`.
- That rerun is the Silver version 8 -> 9 transition; v9 is the idempotency proof. Silver versions v1-v8 are development runs.
- Caveat: `silver_history.png` shows versions 0-8 only, because it was captured before the rerun that created v9. No `DESCRIBE HISTORY` screenshot displays version 9 itself. The v8 -> v9 transition is evidenced by the rerun output (`evidence/day6/silver_rerun_v8_v9.png`), which prints `Versi terakhir sebelum rerun: 8` and then identical snapshots A and B; the new version number is never printed.
- Version numbers moved on afterwards: the Day 6 rerun and the Day 7 backfill added more versions (Silver ended the Day 7 backfill at version 19; see `evidence/day7/07-backfill.md`). The v9 statement above describes the Day 4 test, not the current table version.

## 6. Screenshots

| File | Content | Time (WIB) |
| --- | --- | --- |
| `silver_output_01.png` | `02_silver` output for 2024-01: input 2,964,624, accepted 2,964,550, rejected 74, per-rule failures 56 / 18 | 10:57 |
| `silver_output_02.png` | `02_silver` output for 2024-02: input 3,007,526, accepted 3,007,504, rejected 22, per-rule failures 7 / 15 | 10:58 |
| `silver_duration_check.png` | `MIN`/`MAX` of `pickup_ts` and `trip_duration_min` per month | 10:58 |
| `silver_history.png` | `DESCRIBE HISTORY` of Silver, versions 0-8 | 11:02 |

The same numbers are stored in `04-quality-results.csv`.

## 7. Limits of this evidence

- Rejected rows are counted and dropped; they are not written to a separate rejected-rows table, so they cannot be inspected afterwards without rerunning the transformation.
- Only the numeric and timestamp columns are checked. Zone IDs are not validated against the taxi zone lookup, and negative monetary values are kept.
- There is no unique trip ID, so Silver does not deduplicate; two identical source rows stay two rows.
- The Silver Delta history screenshot stops at v8, so the v9 rerun is proven by the rerun-test output rather than by the history table.
- The screenshots were taken before the notebook comments were translated into English; the code shown in them matches the logic, not the current comment language.

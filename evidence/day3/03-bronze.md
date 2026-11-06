# Day 3 Evidence: Bronze Load and Reruns

Date: 2026-10-31
Environment: Databricks Free Edition (serverless), `workspace.nyc_mobility.bronze_yellow_trips`, partitioned by `source_month`
Time zones: `DESCRIBE HISTORY` timestamps are **UTC**; Databricks screen timestamps (query refresh time in the SQL editor) are **WIB (UTC+7)**.

## 1. Rows per month

Query run in the SQL editor:

```sql
SELECT source_month, COUNT(*) AS n,
       SUM(CASE WHEN date_format(tpep_pickup_datetime, 'yyyy-MM') <> source_month THEN 1 ELSE 0 END) AS outside_month
FROM workspace.nyc_mobility.bronze_yellow_trips
GROUP BY source_month ORDER BY source_month;
```

| source_month | n | Pickups outside the file's month |
| --- | --- | --- |
| 2024-01 | 2,964,624 | 18 |
| 2024-02 | 3,007,526 | 15 |

- Bronze row counts equal the input file row counts for both months.
- The 18 and 15 pickups outside the file month are kept in Bronze unchanged; Silver rejects them with the `pickup_in_source_month` rule.
- The same query was run again after the last rerun and returned the same numbers (see `bronze_row_count_after_rerun.png`, refreshed 6:05 PM WIB).

## 2. Delta history (UTC)

| Version | Timestamp (UTC) | Timestamp (WIB) | Predicate | Rows written | Files removed | Meaning |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 2026-10-31 04:51:59 | 11:51:59 | - | - | - | `CREATE TABLE` from `sql/00_create_tables.sql` |
| 1 | 2026-10-31 08:56:20 | 15:56:20 | `source_month = '2024-01'` | 2,964,624 | 0 | First January load into an empty partition |
| 2 | 2026-10-31 08:57:11 | 15:57:11 | `source_month = '2024-01'` | 2,964,624 | 1 | January rerun with the same file; the one partition file was replaced |
| 3 | 2026-10-31 08:58:20 | 15:58:20 | `source_month = '2024-02'` | 3,007,526 | 0 | First February load into an empty partition |
| 4 | 2026-10-31 09:04:43 | 16:04:43 | `source_month = '2024-01'` | 2,964,624 | 1 | January rerun again; February was not touched |
| 5 | 2026-10-31 11:02:40 | 18:02:40 | `source_month = '2024-02'` | 3,007,526 | 1 | February rerun; January was not touched |

Run order: **January, January, February, January, February.** Every write is `mode("overwrite")` with a `replaceWhere` predicate; there is no append and no overwrite without a predicate.

Version 1 and version 3 removed 0 files because the target partition was still empty, and version 0 is the table creation. A rerun always removed exactly one file, i.e. only the active month's partition file.

The `files_added` column is NULL in every row: the metric name `numAddedFiles` is not populated in this environment. The "Rows written" column comes from `numOutputRows` and `files_removed` from `numRemovedFiles`, which are populated. Do not read the NULL `files_added` as "no file was added".

## 3. Checksum

Business checksum of Bronze, computed with SQL, was identical before and after version 5:

| source_month | SUM(total_amount) | SUM(trip_distance) |
| --- | --- | --- |
| 2024-01 | 79,456,384.28 | 10,827,308.4 |
| 2024-02 | 80,073,615.28 | 11,611,633.16 |

The February rerun (version 5) left both months' checksums unchanged, and the row counts above were unchanged too. `ingested_at` and `source_file` are not part of this checksum because they are load metadata, not business values.

## 4. Screenshots

- `bronze_row_count_before_rerun.png`: rows per month and pickups outside the month, refreshed 3:59 PM WIB (before the February rerun).
- `bronze_row_count_after_rerun.png`: the same query after the February rerun, refreshed 6:05 PM WIB; the numbers are unchanged.
- `bronze_history_v0_v4.png`: `DESCRIBE HISTORY` showing versions 0-4 (before the last February rerun).
- `bronze_history_v0_v5.png`: `DESCRIBE HISTORY` showing versions 0-5 (used for the table in section 2).

## 5. Limits of this evidence

- The January "rerun" evidence (version 2 and version 4) is count-based only; there is no saved `snap_a`/`snap_b` column comparison for Bronze from Day 3. The full rerun comparison is in `evidence/day6/06-rerun-comparison.md`.
- The checksum numbers in section 3 are quoted from the working query result. No screenshot of the Day 3 before/after-v5 query exists. The same January and February Bronze values appear in the Day 7 snapshot (`evidence/day7/snapshot_after_backfill.png`), so the numbers can be re-checked there, but that snapshot is after the backfill, not the Day 3 comparison.
- Bronze keeps source rows exactly as delivered, including the pickups that fall outside the file month and negative monetary values. No deduplication is done because the source has no unique trip ID.
- Delta is atomic per table only; these versions say nothing about Silver and Gold being in step at the same moment.

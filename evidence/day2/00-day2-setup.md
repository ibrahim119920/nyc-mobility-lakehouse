# Day 2 Evidence: Table Setup and Batch Validation

Date: 2026-10-31
Environment: Databricks Free Edition (serverless), catalog `workspace`, schema `nyc_mobility`
Time zones: `DESCRIBE HISTORY` timestamps are **UTC**; Databricks screen timestamps are **WIB (UTC+7)**.

## 1. Delta tables after creation

`DESCRIBE DETAIL` right after `sql/00_create_tables.sql` was run:

- `workspace.nyc_mobility.bronze_yellow_trips`: partitioned by `["source_month"]`, `numFiles` 0.
- `workspace.nyc_mobility.silver_yellow_trips`: partitioned by `["source_month"]`, `numFiles` 0.
- `workspace.nyc_mobility.gold_daily_pickup_zone`: partitioned by `["source_month"]`, `numFiles` 0.
- Bronze and Silver have the `timestampNtz` table feature enabled, because both have `TIMESTAMP_NTZ` columns.

Bronze table creation is Delta version 0 at 2026-10-31 04:51:59 UTC (see `evidence/day3/03-bronze.md`).

No screenshot of this `DESCRIBE DETAIL` output was taken. The partition column and `numFiles 0` above come from the working query result; the rest of the output (location, size, and file count after later loads) is not preserved.

## 2. `00_prepare_batch` validation (five cases)

| Case | Result | Message |
| --- | --- | --- |
| `2024-01` | passes | `OK: 2024-01 /Volumes/workspace/nyc_mobility/raw/yellow/2024-01/yellow_tripdata_2024-01.parquet` |
| `2024-02` | passes | `OK: 2024-02 /Volumes/workspace/nyc_mobility/raw/yellow/2024-02/yellow_tripdata_2024-02.parquet` |
| `2024-1` | rejected | `ValueError: source_month harus YYYY-MM, diterima: '2024-1'` (must be YYYY-MM) |
| `2024-13` | rejected | `ValueError: source_month bukan bulan kalender yang valid: '2024-13'` (not a valid calendar month) |
| `2024-03` | rejected | `FileNotFoundError: Input tidak ditemukan: /Volumes/workspace/nyc_mobility/raw/yellow/2024-03/yellow_tripdata_2024-03.parquet` (input not found) |

Every rejected case failed before any write, and after all cases Bronze / Silver / Gold held 0 / 0 / 0 rows.

Notes on the screenshots:

- `prepare_batch_03.png` shows `2024-13` with the earlier error text `ValueError: unconverted data remains: 3`. It was taken before the explicit calendar-month message was added; the current behaviour is the one in `prepare_batch_05.png`.
- `prepare_batch_05.png` shows `2024-13` again, now with `ValueError: source_month bukan bulan kalender yang valid: '2024-13'`.
- There is no screenshot of the Day 2 `2024-03` validation cell itself. The same `FileNotFoundError` for the `2024-03` file is captured in `evidence/day6/failed_run_detail.png`, where the job's `prepare` task fails on `/Volumes/workspace/nyc_mobility/raw/yellow/2024-03/yellow_tripdata_2024-03.parquet` on 2026-11-05.

### Screenshot map

| File | Case shown | Outcome |
| --- | --- | --- |
| `prepare_batch_01.png` | `2024-01` | passes |
| `prepare_batch_02.png` | `2024-02` | passes |
| `prepare_batch_03.png` | `2024-13` | earlier error text, `unconverted data remains: 3` |
| `prepare_batch_04.png` | `2024-1` | `ValueError: source_month harus YYYY-MM, diterima: '2024-1'` |
| `prepare_batch_05.png` | `2024-13` | `ValueError: source_month bukan bulan kalender yang valid: '2024-13'` |
| `row_count.png` | count query at 3:59 PM WIB | `5,972,150 / 0 / 0`, not the post-validation state |

## 3. Row counts after the validation cases

The intended check was `SELECT` counts on the three tables after the five cases; the result was 0 / 0 / 0.

`row_count.png` does **not** show that state. The screenshot was refreshed at 3:59 PM WIB on 2026-10-31, after the Bronze loads of that afternoon, and shows `bronze_rows = 5,972,150`, `silver_rows = 0`, `gold_rows = 0` (5,972,150 = 2,964,624 + 3,007,526). It therefore proves that Silver and Gold were still empty at that moment, but it does not prove the Bronze = 0 state right after the validation cases. No screenshot of the 0/0/0 count exists; the 0/0/0 result is recorded from the working session only.

## 4. Limits of this evidence

- Five validation cases, all rejected before writing. There is no test of a wrong schema, an empty file, or a valid month whose file is present but unreadable.
- The `2024-13` case appears twice because the error message was improved between the two screenshots; only the later one reflects the current notebook.

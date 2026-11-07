# Batch and table contract

This document describes what the pipeline was built to guarantee. Evidence that it actually behaved this way is in `evidence/`; see `evidence/README.md` for the index.

## Batch identity

One batch = dataset `yellow` + `source_month` (`YYYY-MM`) + one complete monthly Parquet file. The month is the month in the source file name, not the result of extracting pickup timestamps. The same parameter names (`source_month`, `config_path`) are used by the notebooks, the job, and the documentation.

## Layer responsibilities

| Layer | Contents and grain | Write strategy |
| --- | --- | --- |
| Bronze | One row per source row + metadata (`source_month`, `source_file`, `ingested_at`) | Replace the active `source_month`. |
| Silver | Rows passing the quality rules + derived columns (`pickup_date`, `trip_duration_min`) | Recompute and replace the active `source_month`. |
| Gold | One row per `source_month`, `pickup_date`, `pickup_location_id` | Re-aggregate and replace the active `source_month`. |

The three Delta tables are partitioned by `source_month`. With nine months loaded this keeps the batch boundary easy to inspect; the physical layout should be re-evaluated if data volume grows.

## History and reruns

Every write is `mode("overwrite")` + `replaceWhere` with the exact predicate `source_month = 'YYYY-MM'` on tables created beforehand by `sql/00_create_tables.sql`. The month is validated (format and real calendar month) before the predicate is built. There is no append, and no overwrite without a predicate. An explicit schema is used; automatic schema changes are not used as a substitute for schema checks.

Before writing, each notebook requires a complete, non-empty input, and Silver stops if the result is empty. Rerunning with the same file and the same rules keeps the business-column multiset and the aggregates; `ingested_at`, `processed_at`, `source_file`, and the Delta version may change.

A corrected file is processed as a full replacement of that month, so rows removed from the revised source also disappear from that month's results. Other months stay identical.

There is no unique trip ID in the source. Bronze preserves all source rows and Silver preserves the multiplicity of valid rows; rows are not deduplicated. "No duplication on rerun" means a rerun does not add a second copy of the batch, not that the source is free of identical rows.

## Quality rules

The initial Silver rules are:

| Rule | Meaning |
| --- | --- |
| `pickup_not_null` | `tpep_pickup_datetime` is present. |
| `dropoff_not_null` | `tpep_dropoff_datetime` is present. |
| `pu_location_not_null` | `PULocationID` is not null. |
| `distance_non_negative` | `trip_distance >= 0`. |
| `dropoff_not_before_pickup` | Dropoff is not earlier than pickup. |
| `pickup_in_source_month` | Pickup falls inside the file's month. |

Rejected rows are counted per rule and dropped; they are not stored in a separate table. Negative monetary values are kept for analysis, and there are no refund rules, no zone-ID validation, and no duration cap yet (see `docs/schema_notes.md`).

## Failures and concurrency

The pipeline has a single sequential job and a single writer, which avoids run collisions. Delta provides atomic commits per table, not one transaction across the three tables: if Silver or Gold fails, Bronze may already be updated. In that case, rerun the whole workflow for that month after fixing the cause, and consume Gold only after the workflow succeeds. Input must not change mid-run.

## Status

The batch contract above is implemented in `notebooks/*.py` and was exercised in Databricks:

- Month validation and rejected inputs: `evidence/day2/00-day2-setup.md`
- Bronze load, reruns, checksum: `evidence/day3/03-bronze.md`
- Silver rules and counts: `evidence/day4/04-silver.md`
- Gold reconciliation: `evidence/day5/05-gold.md`
- Job runs, February rerun, failed input: `evidence/day6/06-rerun-comparison.md`
- Backfill of 2024-03 to 2024-09: `evidence/day7/07-backfill.md`

Known gaps: the automated tests cover the input-validation notebook and the repository contract, but the Spark transformations are not covered and the quality queries in `sql/01_quality_checks.sql` are still run by hand, and only nine months of one dataset have been processed. For March to September 2024 only row counts, outside-month pickups, dropoff-before-pickup, and schema equality were checked before loading.

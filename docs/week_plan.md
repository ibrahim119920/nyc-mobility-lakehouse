# One-week plan

The plan below is the order the project was actually built in. Evidence for each day is in `evidence/`.

| Day | Focus | Reviewable outcome | Evidence |
| --- | --- | --- | --- |
| 1 | Databricks setup and download of the first two months | Workspace, Volume files, dataset notes | `data/README.md`, `docs/schema_notes.md` |
| 2 | Prepare batch and DDL | Validated parameters and inputs; three empty Delta tables | `evidence/day2/00-day2-setup.md` |
| 3 | Bronze | Two months loaded; rerun replaces only the active partition | `evidence/day3/03-bronze.md` |
| 4 | Silver | Casting, quality rules, accepted/rejected counts | `evidence/day4/04-silver.md` |
| 5 | Gold and SQL analysis | Daily aggregates per zone plus reconciliation | `evidence/day5/05-gold.md` |
| 6 | Job and integration test | January -> February -> February rerun -> failed input, history intact | `evidence/day6/06-rerun-comparison.md` |
| 7 | Backfill and portfolio documentation | March-September 2024 added through the same job; January/February unchanged; twelve analysis queries run for all nine months; README, docs, and evidence matching the actual state | `evidence/day7/07-backfill.md`, `evidence/day7/07-analysis.md` |

The week is done when all three tables hold every processed month (nine months in the end), rerun business results are identical, the other months' partitions are unchanged, a failed input writes no data, and the job runs every stage plus reconciliation.

What is still open: zone-name lookup, automating the quality queries as tests, duration/refund rules, a committed backfill script, and any scheduling. If time is limited, finish idempotency, history, and quality before adding zone lookups, visualizations, optimization, or deployment automation.

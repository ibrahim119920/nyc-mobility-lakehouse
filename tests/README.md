# Test plan

Status: input validation and the repository contract are covered by automated
tests. The acceptance scenarios below are Spark/Databricks integration
scenarios: they were exercised by hand in Databricks and the results are stored
in `evidence/`. Use synthetic fixtures for small iterations and the two monthly
files for integration validation.

## Automated tests

Run from the repository root:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
ruff check .
```

| File | Covers |
| --- | --- |
| `test_prepare_batch.py` | Executes the real `notebooks/00_prepare_batch.py` with stub `dbutils`/`spark` objects: wrong month format, impossible month, missing `config_path`, incomplete config, missing file, empty file, file with no rows, and the valid path that sets `input_path`. |
| `test_repo_contract.py` | Three partitioned Delta tables, a validated month before every `replaceWhere` write, no append, identical widget names, the sequential job chain, no hardcoded workspace path, and resolvable relative Markdown links. |

These tests do not need Spark, Delta, or a workspace. The scenarios below do,
because they assert what the tables contain after a real run.

| Scenario | Expected result |
| --- | --- |
| Month not matching `YYYY-MM`, missing file, wrong schema, empty input | Fails before writing tables; existing data remains intact. |
| Load January then February | Both `source_month` values are available in every table. |
| Rerun February with the same files/rules | Bronze/Silver business-column multiset and Gold results are identical; no extra copies caused by the rerun. |
| Check January after the February load/rerun | January business columns remain identical. |
| Replace the February file with a complete correction | February contents reflect the replacement; January remains identical. |
| Input has null required timestamps, negative duration/distance | Rows are rejected and the counts are recorded; input = accepted + rejected. |
| All input rejected | The job fails without overwriting the Silver/Gold partitions with empty results. |
| Two identical source rows | Both remain counted per the policy of preserving source rows. |
| Gold reconciliation | Unique grain and SUM(trip_count) equal to the number of Silver rows. |
| Failure after Bronze, then full rerun | All layers become consistent again after the workflow succeeds. |

Compare before/after results using two-way `EXCEPT ALL` or a multiset
comparison that preserves multiplicity. Row counts alone do not prove the data
is identical. Ignore ingestion metadata that changes when comparing business
results.

TODO: turn the check queries in `sql/01_quality_checks.sql` into runnable,
parameterised checks. The real results and the input parameters/versions are
already recorded in `evidence/`. Do not mark a scenario as passing before it has
actually been executed.

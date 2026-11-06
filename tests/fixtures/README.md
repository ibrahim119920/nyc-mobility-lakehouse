# Synthetic fixtures

`yellow_trips_sample.csv` is written by hand for development, not a cut of the
actual TLC data. CSV is easy to review in Git; when testing the Bronze reader,
convert it to Parquet with an explicit schema and write the result to a
temporary directory ignored by Git.

| source_month | Rows | Expectation |
| --- | --- | --- |
| 2024-01 | 1-2 identical | Both accepted; not evidence of rerun duplication. |
| 2024-01 | 3 | Rejected: dropoff precedes pickup (`dropoff_not_before_pickup`). |
| 2024-01 | 4 | Rejected: pickup is null (`pickup_not_null`). |
| 2024-02 | 5 | Accepted. |
| 2024-02 | 6 | Rejected: the pickup is 2024-01-31, outside the February file month (`pickup_in_source_month`). |

With the implemented rules: January has 4 inputs, 2 accepted, 2 rejected, and 1
Gold grain with `trip_count = 2`. February has 2 inputs, 1 accepted, 1
rejected, and 1 Gold grain with `trip_count = 1`. These are expectations, not
test results; nothing in `tests/` is automated yet.

The fixture uses a subset of TLC columns plus an added `source_month` to form
the two batches. Split by month and then drop that synthetic column when
creating the Bronze input; the pipeline adds it from the parameter/file name.
Wrong-schema, negative-distance, and empty-input cases still need to be added
when the tests are written.

# Schema and profiling notes

Source: NYC TLC Yellow Taxi Trip Records, January to September 2024, one complete Parquet file per month.
Environment: Databricks Free Edition (serverless), catalog `workspace`, schema `nyc_mobility`.

## 1. Source schema

The January and February files have **identical schemas** (19 columns), so one explicit DDL works for both months. The Day 7 preflight reported the same schema (`SAMA`, "same") for 2024-03 to 2024-09 as well. The two timestamp columns arrive as `timestamp_ntz` and are stored as `TIMESTAMP_NTZ` in Bronze.

| Column | Type in Bronze |
| --- | --- |
| `VendorID` | INT |
| `tpep_pickup_datetime` | TIMESTAMP_NTZ |
| `tpep_dropoff_datetime` | TIMESTAMP_NTZ |
| `passenger_count` | BIGINT |
| `trip_distance` | DOUBLE |
| `RatecodeID` | BIGINT |
| `store_and_fwd_flag` | STRING |
| `PULocationID` | INT |
| `DOLocationID` | INT |
| `payment_type` | BIGINT |
| `fare_amount` | DOUBLE |
| `extra` | DOUBLE |
| `mta_tax` | DOUBLE |
| `tip_amount` | DOUBLE |
| `tolls_amount` | DOUBLE |
| `improvement_surcharge` | DOUBLE |
| `total_amount` | DOUBLE |
| `congestion_surcharge` | DOUBLE |
| `Airport_fee` | DOUBLE |

Bronze adds `source_month` (partition column), `source_file`, and `ingested_at`. Silver keeps a subset and adds `pickup_date` and `trip_duration_min`. The full DDL is in `sql/00_create_tables.sql`.

## 2. Profiling results

| Check | 2024-01 | 2024-02 |
| --- | --- | --- |
| Rows in file | 2,964,624 | 3,007,526 |
| Pickup timestamp outside the file's month | 18 | 15 |
| Dropoff earlier than pickup | 56 | 7 |
| `PULocationID` null | 0 | 0 |
| Negative `trip_distance` | 0 | 0 |
| Schema identical to the other month | yes | yes |

The counts above are the failures found with the same rule definitions Silver uses, which is why they match `evidence/day4/04-quality-results.csv` (56 / 7 and 18 / 15).

### Day 7 preflight, 2024-03 to 2024-09

The backfill checked a smaller set of conditions before loading each month: row count, pickups outside the file's month, dropoff before pickup, and schema equality. Null `PULocationID` and negative `trip_distance` were **not** measured for these months.

| source_month | Rows in file | Pickup outside the month | Dropoff before pickup | Schema same as Bronze | Silver rejected |
| --- | --- | --- | --- | --- | --- |
| 2024-03 | 3,582,628 | 23 | 117 | yes | 140 |
| 2024-04 | 3,514,289 | 9 | 70 | yes | 79 |
| 2024-05 | 3,723,833 | 33 | 42 | yes | 75 |
| 2024-06 | 3,539,193 | 51 | 8 | yes | 59 |
| 2024-07 | 3,076,903 | 47 | 5 | yes | 52 |
| 2024-08 | 2,979,183 | 51 | 9 | yes | 60 |
| 2024-09 | 3,633,030 | 49 | 45 | yes | 94 |

The two failure columns add up exactly to the rejected count in every month (for example 2024-03: 23 + 117 = 140), so no row in these months fails both rules. Source: `evidence/day7/07-backfill.md` and the screenshots listed there.

## 3. What the profiling implies

- **Month boundary.** A small number of pickups fall outside the file's month (18 and 15). The batch identity is the file month, so these rows are rejected by `pickup_in_source_month` rather than reassigned to another month. They stay visible in Bronze.
- **Clock errors.** Dropoff before pickup (56 and 7) is the largest failure group. Silver rejects these rows.
- **Rules with zero failures.** The null-timestamp, null-`PULocationID`, and negative-distance rules removed no rows in these two months. They are kept as guards for later months, not because they cleaned anything here.
- **One rule per row.** No row fails two rules at once, so accepted + rejected = input and the per-rule counts add up to the rejected total exactly.
- **March to September.** The same two rule types are the only ones measured, and dropoff-before-pickup is much larger in March (117) than in the later months (5 to 70). Null `PULocationID` and negative distance were not measured, so the per-rule Silver breakdown for these months is unknown.

## 4. Extreme trip duration

| source_month | Max `trip_duration_min` |
| --- | --- |
| 2024-01 | 9,455.4 |
| 2024-02 | 5,671.98 |

Duration extremes were profiled for all nine months after the Day 7 backfill (`evidence/day7/07-analysis.md`, query 11). Summary: median 11.6-13.9 minutes, p99 60.4-76.8 minutes, maximum 9,767.5 minutes (2024-04); every month has 12-26 trips over 24 hours and 796-1,132 zero-duration trips.

9,455.4 minutes is roughly 6.6 days for one trip; 5,671.98 minutes is roughly 3.9 days. These are almost certainly meter or timestamp errors, but:

- The initial quality rules do **not** cap duration, so these rows are accepted and they also dominate the Gold average duration per zone.
- No threshold has been agreed, and the distribution was not examined further, so no rule was added. Adding one later means choosing a limit (or a percentile) and re-running every loaded month so Gold stays reproducible.
- Because `avg_trip_duration_min` in Gold is a plain average, a single 6-day trip shifts that zone-day average noticeably. Treat the duration average as unreliable until the outliers are handled.

## 5. Open points

- Negative monetary values (for example negative `total_amount`) are kept; there is no refund rule.
- Zone IDs are not validated against the TLC taxi zone lookup, and no zone names are joined.
- There is no unique trip ID in the source, so no deduplication is possible; identical rows stay identical rows.
- `passenger_count`, `RatecodeID`, and `payment_type` are kept as loaded (BIGINT in Bronze, INT in Silver) without domain checks.

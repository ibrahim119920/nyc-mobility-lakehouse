# Day 7 Evidence: Nine-Month Analysis

Date: 2026-11-06, about 22:45-22:47 WIB (when the result files were saved)
Environment: Databricks Free Edition (serverless), SQL editor against `workspace.nyc_mobility` after the Day 7 backfill
Coverage: 2024-01 to 2024-09, nine complete months (274 calendar days), 30,020,554 trips
Time zones: the CSV files contain **no timestamps**; their file modification times are **WIB (UTC+7)**. No Delta timestamp is used in this analysis.

## 1. What this evidence is

`sql/02_analysis.sql` contains 12 descriptive queries. Each query was run in the Databricks SQL editor and its result was exported to one CSV in this folder. The queries use Gold for monthly, daily, weekday, and zone aggregates, and Silver for the hourly, payment-type, and duration detail (Gold does not keep the trip hour or `payment_type`, and the duration tail is measured on Silver rows).

The result files are:

| CSV | SQL query | Rows | Grain |
| --- | --- | --- | --- |
| `analysis_01_monthly_summary.csv` | 1. Monthly summary | 9 | month |
| `analysis_02_trips_per_day_change.csv` | 2. Month-over-month change | 9 | month |
| `analysis_03_daily_trend.csv` | 3. Daily trend | 274 | day |
| `analysis_04_busiest_quietest_day.csv` | 4. Busiest and quietest day | 9 | month |
| `analysis_05_weekday_profile.csv` | 5. Day-of-week pattern | 7 | weekday |
| `analysis_06_top10_zones_monthly.csv` | 6. Top 10 zones per month | 90 | month + zone |
| `analysis_07_top_zones_overall.csv` | 7. Top zones overall | 10 | zone |
| `analysis_08_zone_concentration.csv` | 8. Zone concentration | 9 | month |
| `analysis_09_hourly_profile.csv` | 9. Hourly profile | 48 | day type + hour |
| `analysis_10_payment_types.csv` | 10. Payment type and tipping | 6 | payment type |
| `analysis_11_duration_profile.csv` | 11. Duration outliers | 9 | month |
| `analysis_12_reconciliation.csv` | 12. Reconciliation with rejection rate | 9 | month |

Every result below is quoted from those CSVs. The queries are in `sql/02_analysis.sql`; the CSVs hold results only.

## 2. Monthly summary (query 1)

| source_month | trips | active days | trips/day | `total_amount_sum` | avg total/trip | avg distance (mi) | avg duration (min) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-01 | 2,964,550 | 31 | 95,631 | 79,454,065.50 | 26.80 | 3.65 | 15.6 |
| 2024-02 | 3,007,504 | 29 | 103,707 | 80,073,049.72 | 26.62 | 3.86 | 16.0 |
| 2024-03 | 3,582,488 | 31 | 115,564 | 97,158,149.49 | 27.12 | 4.52 | 16.7 |
| 2024-04 | 3,514,210 | 30 | 117,140 | 96,616,785.96 | 27.49 | 5.28 | 17.0 |
| 2024-05 | 3,723,758 | 31 | 120,121 | 105,659,924.38 | 28.37 | 5.37 | 18.0 |
| 2024-06 | 3,539,134 | 30 | 117,971 | 98,853,108.04 | 27.93 | 5.22 | 17.6 |
| 2024-07 | 3,076,851 | 31 | 99,253 | 86,416,719.61 | 28.09 | 5.11 | 17.2 |
| 2024-08 | 2,979,123 | 31 | 96,101 | 84,223,219.53 | 28.27 | 4.94 | 17.4 |
| 2024-09 | 3,632,936 | 30 | 121,098 | 103,680,692.85 | 28.54 | 5.74 | 18.6 |

- `trips` equals the Silver row count for every month and the Gold `SUM(trip_count)` (see `analysis_12_reconciliation.csv`).
- September has the most trips per day (121,098) and May the second most (120,121); January has the fewest overall (95,631), and August the fewest among the backfilled months (96,101). September also has the highest average fare per trip (28.54) and the highest average distance (5.74 mi).
- `avg_duration_min` is a trip-weighted average of the Gold per-zone averages, `SUM(avg_trip_duration_min * trip_count) / SUM(trip_count)`, not a re-computation from Silver.

## 3. Month-over-month change (query 2)

| source_month | trips/day | change vs previous month |
| --- | --- | --- |
| 2024-01 | 95,631 | - |
| 2024-02 | 103,707 | +8.4% |
| 2024-03 | 115,564 | +11.4% |
| 2024-04 | 117,140 | +1.4% |
| 2024-05 | 120,121 | +2.5% |
| 2024-06 | 117,971 | -1.8% |
| 2024-07 | 99,253 | -15.9% |
| 2024-08 | 96,101 | -3.2% |
| 2024-09 | 121,098 | +26.0% |

The change is computed on trips per day, not on monthly totals, because the months have different lengths. The table is descriptive; no cause for the July drop or the September rise is established here.

## 4. Daily trend (query 3)

- 274 rows, one per day, with `trips` and `total_amount_sum`.
- Example: 2024-01-01 = 81,011 trips and 2,442,761.74 in total amount.
- The lowest day in the file is 2024-07-04 with 61,817 trips; the highest is 2024-05-16 with 143,798 (query 4).

## 5. Busiest and quietest day per month (query 4)

| source_month | Busiest day | Trips | Quietest day | Trips |
| --- | --- | --- | --- | --- |
| 2024-01 | 2024-01-27 | 110,514 | 2024-01-07 | 67,543 |
| 2024-02 | 2024-02-29 | 129,889 | 2024-02-13 | 69,067 |
| 2024-03 | 2024-03-09 | 140,493 | 2024-03-25 | 93,435 |
| 2024-04 | 2024-04-11 | 142,636 | 2024-04-22 | 90,393 |
| 2024-05 | 2024-05-16 | 143,798 | 2024-05-27 | 72,578 |
| 2024-06 | 2024-06-06 | 142,059 | 2024-06-30 | 91,530 |
| 2024-07 | 2024-07-17 | 128,179 | 2024-07-04 | 61,817 |
| 2024-08 | 2024-08-06 | 119,288 | 2024-08-12 | 80,580 |
| 2024-09 | 2024-09-19 | 142,775 | 2024-09-02 | 80,373 |

2024-02-29 is a leap day, so February has 29 active days. The table is descriptive; no cause for the busiest or quietest day is established here.

## 6. Day-of-week pattern (query 5)

Nine months contain 39 or 40 occurrences of each weekday, so the averages are close to comparable.

| Day | Days counted | Avg trips/day | Min | Max |
| --- | --- | --- | --- | --- |
| Sunday | 39 | 98,203 | 67,543 | 120,116 |
| Monday | 40 | 93,753 | 72,578 | 111,636 |
| Tuesday | 39 | 109,011 | 69,067 | 131,794 |
| Wednesday | 39 | 115,793 | 80,419 | 139,771 |
| Thursday | 39 | 121,707 | 61,817 | 143,798 |
| Friday | 39 | 113,301 | 74,136 | 138,324 |
| Saturday | 39 | 115,587 | 75,081 | 142,392 |

Thursday has the highest average and Monday the lowest in this dataset, but the table is descriptive and the differences are not tested for significance.

## 7. Pickup zones (queries 6 and 7)

Zones are still TLC `LocationID` values; there is no zone-name lookup.

Monthly leader (query 6): zone 132 led January, July, August, and September; zone 161 led February, March, and June; zone 237 led April and May.

Top ten zones over all nine months (query 7):

| Zone | Total trips | Share of all trips | Months in top 10 | Best rank | Worst rank |
| --- | --- | --- | --- | --- | --- |
| 132 | 1,470,205 | 4.90% | 9 | 1 | 4 |
| 161 | 1,405,289 | 4.68% | 9 | 1 | 3 |
| 237 | 1,361,142 | 4.53% | 9 | 1 | 3 |
| 236 | 1,239,938 | 4.13% | 9 | 3 | 8 |
| 162 | 1,037,752 | 3.46% | 9 | 4 | 6 |
| 230 | 1,013,374 | 3.38% | 9 | 6 | 8 |
| 186 | 989,786 | 3.30% | 9 | 4 | 9 |
| 138 | 955,780 | 3.18% | 8 | 5 | 11 |
| 142 | 942,802 | 3.14% | 8 | 7 | 11 |
| 170 | 867,802 | 2.89% | 4 | 9 | 12 |

Seven zones are in the monthly top ten in all nine months. Zones 138 and 142 miss one month, and zone 170 only appears four times.

## 8. Zone concentration (query 8)

| source_month | Zones with trips | Share of trips from the top 10 zones |
| --- | --- | --- |
| 2024-01 | 260 | 39.4% |
| 2024-02 | 254 | 37.7% |
| 2024-03 | 259 | 36.6% |
| 2024-04 | 259 | 37.4% |
| 2024-05 | 258 | 38.0% |
| 2024-06 | 260 | 36.8% |
| 2024-07 | 258 | 38.7% |
| 2024-08 | 259 | 38.1% |
| 2024-09 | 258 | 36.7% |

Between 254 and 260 different pickup zones appear per month, and the ten busiest zones account for 36.6% to 39.4% of trips. This is a descriptive concentration measure, not a demand model.

## 9. Hourly profile, weekday vs weekend (query 9)

Silver is used because Gold has no hour column. Averages divide by the number of days of that type, not by the number of rows.

- Weekday peak: 18:00 with 8,282 trips/day. Weekend peak: 17:00 with 6,747.
- Weekend late night is much busier than weekday late night: at 00:00, 5,898 trips/day on weekends versus 2,088 on weekdays; at 01:00, 4,727 versus 1,009.
- Early-morning trips are longer and more expensive: weekday 05:00 averages 20.47 mi and 35.04 in total amount; weekend 05:00 averages 7.22 mi and 36.58.
- The full 48-row table is in `analysis_09_hourly_profile.csv`.

## 10. Payment type and tipping (query 10)

| `payment_type` | Label | Trips | Share | Avg fare | Tip as % of fare |
| --- | --- | --- | --- | --- | --- |
| 1 | Credit card | 22,145,463 | 73.77% | 19.78 | 21.94% |
| 2 | Cash | 4,122,198 | 13.73% | 18.52 | 0.02% |
| 0 | Other (see data dictionary) | 2,997,101 | 9.98% | 19.62 | 3.65% |
| 4 | Dispute | 547,378 | 1.82% | 1.98 | 2.46% |
| 3 | No charge | 208,410 | 0.69% | 6.53 | 0.31% |
| 5 | Unknown | 4 | 0.00% | 15.50 | 0.00% |

The six rows add up to 30,020,554 trips, which matches the monthly summary. Cash tips are not recorded in the source, so the 0.02% for cash is not evidence that cash passengers do not tip. The labels follow the TLC data dictionary; `payment_type = 0` is left as "Other" instead of guessing a meaning.

## 11. Duration profile (query 11)

Silver is used because it holds `trip_duration_min`. The quality rules still do not cap duration.

| source_month | Trips | Zero duration | Over 3 h | Over 24 h | Median (min) | p99 (min) | Max (min) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-01 | 2,964,550 | 814 | 1,983 | 16 | 11.6 | 60.4 | 9,455.4 |
| 2024-02 | 3,007,504 | 796 | 1,948 | 12 | 12.0 | 62.4 | 5,672.0 |
| 2024-03 | 3,582,488 | 1,011 | 2,171 | 20 | 12.5 | 67.2 | 9,092.6 |
| 2024-04 | 3,514,210 | 1,019 | 2,260 | 26 | 12.8 | 67.6 | 9,767.5 |
| 2024-05 | 3,723,758 | 1,105 | 2,299 | 15 | 13.3 | 75.5 | 8,547.7 |
| 2024-06 | 3,539,134 | 1,132 | 2,222 | 20 | 13.0 | 72.9 | 7,658.6 |
| 2024-07 | 3,076,851 | 1,063 | 2,049 | 25 | 12.8 | 67.7 | 9,670.3 |
| 2024-08 | 2,979,123 | 1,009 | 2,089 | 24 | 12.8 | 69.4 | 9,027.1 |
| 2024-09 | 3,632,936 | 1,116 | 1,963 | 25 | 13.9 | 76.8 | 7,234.3 |

- Zero-duration trips exist in every month (796 to 1,132), so `dropoff = pickup` is not filtered.
- Trips over 24 hours exist in every month (12 to 26). The largest single value is 9,767.5 minutes (about 6.8 days) in 2024-04, larger than the January maximum of 9,455.4.
- 99% of trips are at or below 60.4-76.8 minutes, so the extreme values are a very small tail; they are still kept and they still skew `avg_trip_duration_min` in Gold.
- This table is the evidence needed to choose a duration rule later; no rule has been added.

## 12. Reconciliation with rejection rate (query 12)

| source_month | Bronze | Rejected | Rejected % | Silver | Gold trips | `gold_diff` | Gold rows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-01 | 2,964,624 | 74 | 0.00250 | 2,964,550 | 2,964,550 | 0 | 6,949 |
| 2024-02 | 3,007,526 | 22 | 0.00073 | 3,007,504 | 3,007,504 | 0 | 6,499 |
| 2024-03 | 3,582,628 | 140 | 0.00391 | 3,582,488 | 3,582,488 | 0 | 7,180 |
| 2024-04 | 3,514,289 | 79 | 0.00225 | 3,514,210 | 3,514,210 | 0 | 6,943 |
| 2024-05 | 3,723,833 | 75 | 0.00201 | 3,723,758 | 3,723,758 | 0 | 7,260 |
| 2024-06 | 3,539,193 | 59 | 0.00167 | 3,539,134 | 3,539,134 | 0 | 6,993 |
| 2024-07 | 3,076,903 | 52 | 0.00169 | 3,076,851 | 3,076,851 | 0 | 7,191 |
| 2024-08 | 2,979,183 | 60 | 0.00201 | 2,979,123 | 2,979,123 | 0 | 7,267 |
| 2024-09 | 3,633,030 | 94 | 0.00259 | 3,632,936 | 3,632,936 | 0 | 7,097 |

`rejected_pct` is already a percentage: 0.0025 means 0.0025%, not 0.25%. The rejection rate is below 0.004% in every month. `gold_diff` is 0 everywhere.

For 2024-05 the Gold `SUM(total_amount)` (105,659,924.38) is lower than Bronze (105,662,803.20) by 2,878.82. That is consistent with Gold being built from the accepted rows after the rejected rows are dropped; it is not a reconciliation error. The same direction holds in every month.

## 13. Limits of this evidence

- The results are descriptive. No hypothesis test, confidence interval, or causal claim is made.
- Zones are numeric IDs. "Top zone" cannot be named, and the concentration figure says nothing about why those zones are busy.
- The hourly, payment, and duration queries run on Silver; the rest run on Gold. Gold aggregates by day and zone, so it cannot answer questions that need the hour, the payment type, or a single trip.
- Cash tips are not in the source, so the tip percentage is only meaningful for credit-card trips.
- The CSVs are result exports. They do not contain the SQL text, the run timestamp, or a query ID; the query text lives in `sql/02_analysis.sql`, and the export time is only the file modification time (WIB).
- The nine months are January to September 2024, not a full year; October to December are not loaded, so no seasonality claim about a full year is possible.
- `2024-02-29` is a leap day; the busiest/quietest table does not test calendar or holiday effects.

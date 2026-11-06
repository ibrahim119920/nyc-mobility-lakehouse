-- 02_analysis.sql
-- Descriptive analysis on Gold (and Silver where hourly / payment detail is needed).
-- Coverage: NYC TLC Yellow Taxi, 2024-01 to 2024-09 (nine months, not a full year).
-- Zones are still TLC LocationIDs; there is no zone-name lookup yet.
-- Results are descriptive. They do not explain causes.

-- ---------------------------------------------------------------------------
-- 1. Monthly summary (Gold)
--    trips_per_day is used because months have different lengths.
-- ---------------------------------------------------------------------------
SELECT source_month,
       SUM(trip_count)                                              AS trips,
       COUNT(DISTINCT pickup_date)                                  AS active_days,
       ROUND(SUM(trip_count) / COUNT(DISTINCT pickup_date))         AS trips_per_day,
       ROUND(SUM(total_amount), 2)                                  AS total_amount_sum,
       ROUND(SUM(total_amount) / SUM(trip_count), 2)                AS avg_total_amount_per_trip,
       ROUND(SUM(total_distance) / SUM(trip_count), 2)              AS avg_distance_mi,
       ROUND(SUM(avg_trip_duration_min * trip_count) / SUM(trip_count), 1) AS avg_duration_min
FROM workspace.nyc_mobility.gold_daily_pickup_zone
GROUP BY source_month
ORDER BY source_month;

-- ---------------------------------------------------------------------------
-- 2. Month-over-month change in trips per day (Gold)
-- ---------------------------------------------------------------------------
WITH m AS (
  SELECT source_month,
         SUM(trip_count) / COUNT(DISTINCT pickup_date) AS trips_per_day
  FROM workspace.nyc_mobility.gold_daily_pickup_zone
  GROUP BY source_month
)
SELECT source_month,
       ROUND(trips_per_day) AS trips_per_day,
       ROUND(100 * (trips_per_day / LAG(trips_per_day) OVER (ORDER BY source_month) - 1), 1) AS pct_change_vs_prev_month
FROM m
ORDER BY source_month;

-- ---------------------------------------------------------------------------
-- 3. Daily trend (Gold) -- line chart: X = pickup_date, Y = trips
-- ---------------------------------------------------------------------------
SELECT source_month, pickup_date,
       SUM(trip_count)                 AS trips,
       ROUND(SUM(total_amount), 2)     AS total_amount_sum
FROM workspace.nyc_mobility.gold_daily_pickup_zone
GROUP BY source_month, pickup_date
ORDER BY pickup_date;

-- ---------------------------------------------------------------------------
-- 4. Busiest and quietest day per month (Gold)
-- ---------------------------------------------------------------------------
WITH daily AS (
  SELECT source_month, pickup_date, SUM(trip_count) AS trips
  FROM workspace.nyc_mobility.gold_daily_pickup_zone
  GROUP BY source_month, pickup_date
)
SELECT source_month,
       max_by(pickup_date, trips) AS busiest_day,
       MAX(trips)                 AS busiest_day_trips,
       min_by(pickup_date, trips) AS quietest_day,
       MIN(trips)                 AS quietest_day_trips
FROM daily
GROUP BY source_month
ORDER BY source_month;

-- ---------------------------------------------------------------------------
-- 5. Day-of-week pattern (Gold): average trips per calendar day, all nine months
-- ---------------------------------------------------------------------------
WITH daily AS (
  SELECT pickup_date, SUM(trip_count) AS trips
  FROM workspace.nyc_mobility.gold_daily_pickup_zone
  GROUP BY pickup_date
)
SELECT dayofweek(pickup_date)             AS dow_num,   -- 1 = Sunday ... 7 = Saturday
       date_format(pickup_date, 'EEEE')   AS weekday,
       COUNT(*)                           AS days_counted,
       ROUND(AVG(trips))                  AS avg_trips_per_day,
       MIN(trips)                         AS min_trips,
       MAX(trips)                         AS max_trips
FROM daily
GROUP BY dayofweek(pickup_date), date_format(pickup_date, 'EEEE')
ORDER BY dow_num;

-- ---------------------------------------------------------------------------
-- 6. Top 10 pickup zones per month (Gold)
-- ---------------------------------------------------------------------------
SELECT source_month, pickup_location_id, trips_month, rn AS rank_in_month
FROM (
  SELECT source_month, pickup_location_id,
         SUM(trip_count) AS trips_month,
         ROW_NUMBER() OVER (PARTITION BY source_month ORDER BY SUM(trip_count) DESC) AS rn
  FROM workspace.nyc_mobility.gold_daily_pickup_zone
  GROUP BY source_month, pickup_location_id
)
WHERE rn <= 10
ORDER BY source_month, rn;

-- ---------------------------------------------------------------------------
-- 7. Top 10 zones overall and how stable their rank is (Gold)
-- ---------------------------------------------------------------------------
WITH z AS (
  SELECT source_month, pickup_location_id,
         SUM(trip_count) AS trips,
         ROW_NUMBER() OVER (PARTITION BY source_month ORDER BY SUM(trip_count) DESC) AS rn
  FROM workspace.nyc_mobility.gold_daily_pickup_zone
  GROUP BY source_month, pickup_location_id
)
SELECT pickup_location_id,
       SUM(trips)                                                   AS total_trips,
       ROUND(100 * SUM(trips) / (SELECT SUM(trip_count) FROM workspace.nyc_mobility.gold_daily_pickup_zone), 2) AS share_pct,
       SUM(CASE WHEN rn <= 10 THEN 1 ELSE 0 END)                    AS months_in_top10,
       MIN(rn)                                                      AS best_rank,
       MAX(rn)                                                      AS worst_rank
FROM z
GROUP BY pickup_location_id
ORDER BY total_trips DESC
LIMIT 10;

-- ---------------------------------------------------------------------------
-- 8. Concentration: share of monthly trips from the 10 busiest zones (Gold)
-- ---------------------------------------------------------------------------
WITH z AS (
  SELECT source_month, pickup_location_id,
         SUM(trip_count) AS trips,
         ROW_NUMBER() OVER (PARTITION BY source_month ORDER BY SUM(trip_count) DESC) AS rn
  FROM workspace.nyc_mobility.gold_daily_pickup_zone
  GROUP BY source_month, pickup_location_id
)
SELECT source_month,
       COUNT(*)                                                    AS zones_with_trips,
       ROUND(100 * SUM(CASE WHEN rn <= 10 THEN trips END) / SUM(trips), 1) AS top10_share_pct
FROM z
GROUP BY source_month
ORDER BY source_month;

-- ---------------------------------------------------------------------------
-- 9. Hourly profile, weekday vs weekend (Silver)
--    avg_trips_per_day divides by the number of days of that type, so the two
--    day types are comparable.
-- ---------------------------------------------------------------------------
SELECT CASE WHEN dayofweek(pickup_date) IN (1, 7) THEN 'weekend' ELSE 'weekday' END AS day_type,
       hour(pickup_ts)                                  AS pickup_hour,
       ROUND(COUNT(*) / COUNT(DISTINCT pickup_date))    AS avg_trips_per_day,
       ROUND(AVG(total_amount), 2)                      AS avg_total_amount,
       ROUND(AVG(trip_distance), 2)                     AS avg_distance_mi
FROM workspace.nyc_mobility.silver_yellow_trips
GROUP BY 1, 2
ORDER BY 1, 2;

-- ---------------------------------------------------------------------------
-- 10. Payment type and tipping (Silver)
--     Labels follow the TLC data dictionary (verify against the current version).
--     Cash tips are not recorded in the data, so tip_pct_of_fare is meaningful
--     for credit-card trips only.
-- ---------------------------------------------------------------------------
SELECT payment_type,
       CASE payment_type
         WHEN 1 THEN 'Credit card' WHEN 2 THEN 'Cash' WHEN 3 THEN 'No charge'
         WHEN 4 THEN 'Dispute'     WHEN 5 THEN 'Unknown' WHEN 6 THEN 'Voided trip'
         ELSE 'Other (see data dictionary)'
       END                                                          AS payment_label,
       COUNT(*)                                                     AS trips,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)             AS share_pct,
       ROUND(AVG(fare_amount), 2)                                   AS avg_fare,
       ROUND(100 * SUM(tip_amount) / NULLIF(SUM(fare_amount), 0), 2) AS tip_pct_of_fare
FROM workspace.nyc_mobility.silver_yellow_trips
GROUP BY payment_type
ORDER BY trips DESC;

-- ---------------------------------------------------------------------------
-- 11. Duration outliers per month (Silver)
--     The initial quality rules do not cap duration. This query sizes the tail
--     and supports a candidate duration rule.
-- ---------------------------------------------------------------------------
SELECT source_month,
       COUNT(*)                                                        AS trips,
       SUM(CASE WHEN trip_duration_min = 0    THEN 1 ELSE 0 END)       AS zero_duration,
       SUM(CASE WHEN trip_duration_min > 180  THEN 1 ELSE 0 END)       AS over_3h,
       SUM(CASE WHEN trip_duration_min > 1440 THEN 1 ELSE 0 END)       AS over_24h,
       ROUND(percentile_approx(trip_duration_min, 0.5), 1)             AS median_min,
       ROUND(percentile_approx(trip_duration_min, 0.99), 1)            AS p99_min,
       ROUND(MAX(trip_duration_min), 1)                                AS max_min
FROM workspace.nyc_mobility.silver_yellow_trips
GROUP BY source_month
ORDER BY source_month;

-- ---------------------------------------------------------------------------
-- 12. Reconciliation Bronze -> Silver -> Gold, with rejection rate
--     gold_diff must be 0 for every month.
-- ---------------------------------------------------------------------------
WITH b AS (SELECT source_month, COUNT(*) AS bronze_rows
           FROM workspace.nyc_mobility.bronze_yellow_trips GROUP BY source_month),
     s AS (SELECT source_month, COUNT(*) AS silver_rows
           FROM workspace.nyc_mobility.silver_yellow_trips GROUP BY source_month),
     g AS (SELECT source_month, COUNT(*) AS gold_rows, SUM(trip_count) AS gold_trips
           FROM workspace.nyc_mobility.gold_daily_pickup_zone GROUP BY source_month)
SELECT source_month, bronze_rows,
       bronze_rows - silver_rows                                  AS rejected,
       ROUND(100 * (bronze_rows - silver_rows) / bronze_rows, 5)  AS rejected_pct,
       silver_rows, gold_trips,
       silver_rows - gold_trips                                   AS gold_diff,
       gold_rows
FROM b JOIN s USING (source_month) JOIN g USING (source_month)
ORDER BY source_month;
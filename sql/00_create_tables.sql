-- DDL used to create the three tables once, before the first workflow run.
-- All tables use USING DELTA and PARTITIONED BY (source_month). The catalog
-- and schema come from config/batch.local.json; the names below are the ones
-- used in this project (workspace.nyc_mobility).
-- Do not DROP/CREATE the tables on every batch: the Delta history has to survive.
--
-- bronze_yellow_trips:
--   Original TLC columns + source_month STRING, source_file STRING, ingested_at TIMESTAMP.
--   The two source timestamp columns are TIMESTAMP_NTZ.
-- silver_yellow_trips:
--   Selected and cast columns + source_month, processed_at,
--   pickup_date DATE, trip_duration_min DOUBLE.
-- gold_daily_pickup_zone:
--   source_month STRING, pickup_date DATE, pickup_location_id INT,
--   trip_count BIGINT, total_distance DOUBLE, total_amount DOUBLE.
--   Gold grain: (source_month, pickup_date, pickup_location_id).

CREATE TABLE IF NOT EXISTS workspace.nyc_mobility.bronze_yellow_trips (
  VendorID INT,
  tpep_pickup_datetime TIMESTAMP_NTZ,
  tpep_dropoff_datetime TIMESTAMP_NTZ,
  passenger_count BIGINT,
  trip_distance DOUBLE,
  RatecodeID BIGINT,
  store_and_fwd_flag STRING,
  PULocationID INT,
  DOLocationID INT,
  payment_type BIGINT,
  fare_amount DOUBLE,
  extra DOUBLE,
  mta_tax DOUBLE,
  tip_amount DOUBLE,
  tolls_amount DOUBLE,
  improvement_surcharge DOUBLE,
  total_amount DOUBLE,
  congestion_surcharge DOUBLE,
  Airport_fee DOUBLE,
  source_month STRING NOT NULL,
  source_file STRING,
  ingested_at TIMESTAMP
) USING DELTA PARTITIONED BY (source_month);

CREATE TABLE IF NOT EXISTS workspace.nyc_mobility.silver_yellow_trips (
  VendorID INT,
  pickup_ts TIMESTAMP_NTZ NOT NULL,
  dropoff_ts TIMESTAMP_NTZ NOT NULL,
  passenger_count INT,
  trip_distance DOUBLE,
  pickup_location_id INT NOT NULL,
  dropoff_location_id INT,
  payment_type INT,
  fare_amount DOUBLE,
  tip_amount DOUBLE,
  total_amount DOUBLE,
  pickup_date DATE,
  trip_duration_min DOUBLE,
  source_month STRING NOT NULL,
  processed_at TIMESTAMP
) USING DELTA PARTITIONED BY (source_month);

CREATE TABLE IF NOT EXISTS workspace.nyc_mobility.gold_daily_pickup_zone (
  source_month STRING NOT NULL,
  pickup_date DATE NOT NULL,
  pickup_location_id INT NOT NULL,
  trip_count BIGINT,
  total_distance DOUBLE,
  total_fare_amount DOUBLE,
  total_amount DOUBLE,
  avg_trip_duration_min DOUBLE
) USING DELTA PARTITIONED BY (source_month);

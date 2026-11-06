# Databricks notebook source
import json, re
from datetime import datetime
from pyspark.sql import functions as F

dbutils.widgets.text("source_month", "")
dbutils.widgets.text("config_path", "")
source_month = dbutils.widgets.get("source_month").strip()
config_path = dbutils.widgets.get("config_path").strip()

# Validate the month before building the replaceWhere predicate
if not re.fullmatch(r"\d{4}-\d{2}", source_month):
    raise ValueError(f"source_month harus YYYY-MM, diterima: {source_month!r}")
try:
    datetime.strptime(source_month, "%Y-%m")
except ValueError:
    raise ValueError(f"source_month bukan bulan kalender yang valid: {source_month!r}")

with open(config_path) as f:
    cfg = json.load(f)
fq = lambda k: f"{cfg['catalog']}.{cfg['schema']}.{cfg['tables'][k]}"
silver, gold = fq("silver"), fq("gold")

src = spark.table(silver).where(F.col("source_month") == source_month)

agg = (src.groupBy("source_month", "pickup_date", "pickup_location_id")
    .agg(
        F.count("*").alias("trip_count"),
        F.sum("trip_distance").alias("total_distance"),
        F.sum("fare_amount").alias("total_fare_amount"),
        F.sum("total_amount").alias("total_amount"),
        F.avg("trip_duration_min").alias("avg_trip_duration_min"),
    ))

# Columns must match the table exactly: fail early if they do not
agg = agg.select(*spark.table(gold).columns)

silver_rows = src.count()
if silver_rows == 0:
    raise ValueError("Silver kosong untuk bulan ini, run dihentikan untuk diperiksa")

(agg.write.format("delta").mode("overwrite")
    .option("replaceWhere", f"source_month = '{source_month}'")
    .saveAsTable(gold))

# Reconciliation: Gold must sum to Silver
g = (spark.table(gold).where(F.col("source_month") == source_month)
     .agg(F.count("*").alias("gold_rows"),
          F.sum("trip_count").alias("sum_trip_count")).first())
if g["sum_trip_count"] != silver_rows:
    raise RuntimeError(f"Rekonsiliasi gagal: Silver {silver_rows}, SUM(trip_count) Gold {g['sum_trip_count']}")

print(f"Gold OK: {source_month}")
print(f"  silver_rows: {silver_rows}")
print(f"  gold_rows: {g['gold_rows']}")
print(f"  sum_trip_count: {g['sum_trip_count']}")
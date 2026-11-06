# Databricks notebook source
import json, re
from datetime import datetime
from pyspark.sql import functions as F

dbutils.widgets.text("source_month", "")
dbutils.widgets.text("config_path", "")
source_month = dbutils.widgets.get("source_month").strip()
config_path = dbutils.widgets.get("config_path").strip()

if not re.fullmatch(r"\d{4}-\d{2}", source_month):
    raise ValueError(f"source_month harus YYYY-MM, diterima: {source_month!r}")
try:
    datetime.strptime(source_month, "%Y-%m")
except ValueError:
    raise ValueError(f"source_month bukan bulan kalender yang valid: {source_month!r}")

with open(config_path) as f:
    cfg = json.load(f)
fq = lambda k: f"{cfg['catalog']}.{cfg['schema']}.{cfg['tables'][k]}"
bronze, silver = fq("bronze"), fq("silver")

src = spark.table(bronze).where(F.col("source_month") == source_month)

start = F.lit(f"{source_month}-01").cast("date")
pickup, dropoff = F.col("tpep_pickup_datetime"), F.col("tpep_dropoff_datetime")

# Quality rules: True = passes
rules = {
    "pickup_not_null":      pickup.isNotNull(),
    "dropoff_not_null":     dropoff.isNotNull(),
    "pu_location_not_null": F.col("PULocationID").isNotNull(),
    "distance_non_negative": F.col("trip_distance") >= 0,
    "dropoff_not_before_pickup": dropoff >= pickup,
    "pickup_in_source_month": (pickup >= start.cast("timestamp_ntz"))
                              & (pickup < F.add_months(start, 1).cast("timestamp_ntz")),
}
# NULL on a rule counts as a failure
checked = src
for name, cond in rules.items():
    checked = checked.withColumn(f"ok_{name}", F.coalesce(cond, F.lit(False)))
ok_cols = [f"ok_{n}" for n in rules]
all_ok = F.expr(" AND ".join(ok_cols))
checked = checked.withColumn("is_valid", all_ok).cache()

n_in = checked.count()
if n_in == 0:
    raise ValueError("Bronze kosong untuk bulan ini")

# Metrics per rule (one row can fail more than one rule)
metrics = checked.agg(
    F.count("*").alias("input_rows"),
    F.sum(F.col("is_valid").cast("int")).alias("accepted_rows"),
    *[F.sum((~F.col(c)).cast("int")).alias("fail_" + c[3:]) for c in ok_cols],
).first().asDict()
metrics["rejected_rows"] = metrics["input_rows"] - metrics["accepted_rows"]

good = (checked.where("is_valid")
    .select(
        F.col("VendorID"),
        pickup.alias("pickup_ts"),
        dropoff.alias("dropoff_ts"),
        F.col("passenger_count").cast("int"),
        F.col("trip_distance"),
        F.col("PULocationID").alias("pickup_location_id"),
        F.col("DOLocationID").alias("dropoff_location_id"),
        F.col("payment_type").cast("int"),
        F.col("fare_amount"), F.col("tip_amount"), F.col("total_amount"),
        F.to_date(pickup).alias("pickup_date"),
        ((F.unix_timestamp(dropoff.cast("timestamp")) - F.unix_timestamp(pickup.cast("timestamp"))) / 60.0).alias("trip_duration_min"),
        F.lit(source_month).alias("source_month"),
        F.current_timestamp().alias("processed_at"),
    ))

if metrics["accepted_rows"] == 0:
    raise ValueError("Hasil Silver kosong, run dihentikan untuk diperiksa")

(good.write.format("delta").mode("overwrite")
     .option("replaceWhere", f"source_month = '{source_month}'")
     .saveAsTable(silver))

n_out = spark.table(silver).where(F.col("source_month") == source_month).count()
if n_out != metrics["accepted_rows"]:
    raise RuntimeError(f"Rekonsiliasi gagal: diterima {metrics['accepted_rows']}, Silver {n_out}")

print(f"Silver OK: {source_month}")
for k, v in metrics.items():
    print(f"  {k}: {v}")
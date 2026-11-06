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

input_path = f"{cfg['raw_root']}/{source_month}/{cfg['dataset']}_tripdata_{source_month}.parquet"
target = f"{cfg['catalog']}.{cfg['schema']}.{cfg['tables']['bronze']}"

df = (
    spark.read.parquet(input_path)
    .withColumn("source_month", F.lit(source_month))
    .withColumn("source_file", F.lit(input_path))
    .withColumn("ingested_at", F.current_timestamp())
)

# Columns must match the table exactly: fail early if they do not
target_cols = spark.table(target).columns
df = df.select(*target_cols)

n_in = df.count()
if n_in == 0:
    raise ValueError("Input kosong, tidak ada yang ditulis")

(df.write
   .format("delta")
   .mode("overwrite")
   .option("replaceWhere", f"source_month = '{source_month}'")
   .saveAsTable(target))

n_out = spark.table(target).where(F.col("source_month") == source_month).count()
if n_out != n_in:
    raise RuntimeError(f"Rekonsiliasi gagal: input {n_in}, Bronze {n_out}")
print(f"Bronze OK: {source_month}, {n_out} baris")
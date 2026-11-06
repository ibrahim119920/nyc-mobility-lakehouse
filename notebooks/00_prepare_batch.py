
# Databricks notebook source
import json, os, re
from datetime import datetime

dbutils.widgets.text("source_month", "")
dbutils.widgets.text("config_path", "")

source_month = dbutils.widgets.get("source_month").strip()
config_path = dbutils.widgets.get("config_path").strip()

# 1. Validate the month: format and a real calendar month
if not re.fullmatch(r"\d{4}-\d{2}", source_month):
    raise ValueError(f"source_month harus YYYY-MM, diterima: {source_month!r}")
try:
    datetime.strptime(source_month, "%Y-%m")
except ValueError:
    raise ValueError(f"source_month bukan bulan kalender yang valid: {source_month!r}")

# 2. Read and validate the configuration
if not config_path:
    raise ValueError("config_path wajib diisi")
with open(config_path) as f:
    cfg = json.load(f)
for key in ["dataset", "catalog", "schema", "raw_root", "tables"]:
    if key not in cfg:
        raise KeyError(f"Konfigurasi tidak memuat '{key}'")

# 3. Validate the input: the file exists, is not empty, and has at least one row
input_path = f"{cfg['raw_root']}/{source_month}/{cfg['dataset']}_tripdata_{source_month}.parquet"
if not os.path.exists(input_path):
    raise FileNotFoundError(f"Input tidak ditemukan: {input_path}")
if os.path.getsize(input_path) == 0:
    raise ValueError(f"File kosong: {input_path}")
if spark.read.parquet(input_path).limit(1).count() == 0:
    raise ValueError(f"File tidak berisi baris: {input_path}")

# 4. Pass the value to the next task (only works inside a Job)
try:
    dbutils.jobs.taskValues.set(key="input_path", value=input_path)
except Exception:
    pass

print("OK:", source_month, input_path)
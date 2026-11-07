"""Repository-level contract checks that do not need Spark or Databricks.

These tests guard the invariants the documentation promises: three partitioned
Delta tables, a validated month before every ``replaceWhere`` write, one
sequential job, and no broken relative links in the Markdown files.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ["00_prepare_batch.py", "01_bronze.py", "02_silver.py", "03_gold.py"]
WRITERS = ["01_bronze.py", "02_silver.py", "03_gold.py"]
TABLES = {"bronze": "bronze_yellow_trips",
          "silver": "silver_yellow_trips",
          "gold": "gold_daily_pickup_zone"}


def read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def test_ddl_creates_the_three_partitioned_delta_tables() -> None:
    ddl = read("sql/00_create_tables.sql")

    for table in TABLES.values():
        assert re.search(rf"CREATE TABLE IF NOT EXISTS [\w.]+\.{table}\b", ddl), table
    assert ddl.count("USING DELTA PARTITIONED BY (source_month)") == 3
    assert "DROP TABLE" not in ddl.upper()


def test_every_notebook_takes_the_same_two_widgets() -> None:
    for name in NOTEBOOKS:
        source = read(f"notebooks/{name}")
        assert 'dbutils.widgets.text("source_month", "")' in source, name
        assert 'dbutils.widgets.text("config_path", "")' in source, name


def test_every_writer_validates_the_month_before_writing() -> None:
    for name in WRITERS:
        source = read(f"notebooks/{name}")
        assert r"\d{4}-\d{2}" in source, name
        assert 'datetime.strptime(source_month, "%Y-%m")' in source, name


def test_every_write_is_a_predicated_overwrite() -> None:
    for name in WRITERS:
        source = read(f"notebooks/{name}")
        assert 'mode("overwrite")' in source, name
        assert 'replaceWhere' in source, name
        assert 'f"source_month = \'{source_month}\'"' in source, name
        assert 'mode("append")' not in source, name


def test_config_example_matches_the_expected_keys() -> None:
    config = json.loads(read("config/batch.example.json"))

    assert {"dataset", "catalog", "schema", "raw_root", "tables"} <= set(config)
    assert config["tables"] == TABLES


def test_job_is_one_sequential_chain_with_a_single_writer() -> None:
    job = json.loads(read("jobs/monthly_job.example.json"))

    assert job["max_concurrent_runs"] == 1
    assert {task["task_key"] for task in job["tasks"]} == {
        "prepare", "bronze", "silver", "gold"
    }
    tasks = {task["task_key"]: task for task in job["tasks"]}
    assert "depends_on" not in tasks["prepare"]
    assert tasks["bronze"]["depends_on"] == [{"task_key": "prepare"}]
    assert tasks["silver"]["depends_on"] == [{"task_key": "bronze"}]
    assert tasks["gold"]["depends_on"] == [{"task_key": "silver"}]
    assert all(task["run_if"] == "ALL_SUCCESS" for task in job["tasks"])
    assert {p["name"] for p in job["parameters"]} == {"source_month", "config_path"}


def test_markdown_relative_links_resolve() -> None:
    failures: list[str] = []
    for markdown in REPO_ROOT.rglob("*.md"):
        if ".git" in markdown.parts:
            continue
        text = markdown.read_text(encoding="utf-8")
        for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            resolved = (markdown.parent / target).resolve()
            if not resolved.exists():
                failures.append(f"{markdown.relative_to(REPO_ROOT)} -> {target}")

    assert not failures, "Broken relative links:\n" + "\n".join(failures)


@pytest.mark.parametrize("name", NOTEBOOKS)
def test_notebook_does_not_hardcode_a_workspace_path(name: str) -> None:
    source = read(f"notebooks/{name}")
    assert "/Workspace/Users/" not in source, name
    assert "dbfs:/" not in source, name

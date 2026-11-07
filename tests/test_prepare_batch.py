"""Execute the real ``00_prepare_batch`` notebook with stubbed platform objects.

Every rejection path that the Day 2 evidence records is asserted here against
the notebook source itself, so the messages cannot drift from the evidence
without the tests failing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import run_notebook


def write_config(tmp_path: Path, **overrides: object) -> Path:
    config = {
        "dataset": "yellow",
        "catalog": "workspace",
        "schema": "nyc_mobility",
        "raw_root": str(tmp_path / "raw"),
        "tables": {"bronze": "bronze_yellow_trips",
                   "silver": "silver_yellow_trips",
                   "gold": "gold_daily_pickup_zone"},
    }
    config.update(overrides)
    path = tmp_path / "batch.local.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def write_input(tmp_path: Path, month: str, payload: bytes = b"PAR1") -> Path:
    folder = tmp_path / "raw" / month
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"yellow_tripdata_{month}.parquet"
    path.write_bytes(payload)
    return path


def run(tmp_path: Path, month: str = "2024-01", config: Path | None = None,
        rows: int = 1) -> tuple[object, dict[str, object]]:
    config = config or write_config(tmp_path)
    return run_notebook(
        "00_prepare_batch.py",
        values={"source_month": month, "config_path": str(config)},
        rows=rows,
    )


def test_valid_month_reports_the_input_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = write_input(tmp_path, "2024-01")

    dbutils, _ = run(tmp_path)

    assert Path(str(dbutils.jobs.taskValues.values["input_path"])) == input_path
    output = capsys.readouterr().out
    assert "OK: 2024-01" in output
    assert input_path.name in output


def test_month_with_wrong_format_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="harus YYYY-MM"):
        run(tmp_path, month="2024-1")


def test_impossible_calendar_month_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="bukan bulan kalender yang valid"):
        run(tmp_path, month="2024-13")


def test_missing_config_path_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="config_path wajib diisi"):
        run_notebook("00_prepare_batch.py",
                     values={"source_month": "2024-01", "config_path": ""})


def test_config_without_a_required_key_is_rejected(tmp_path: Path) -> None:
    config = write_config(tmp_path)
    data = json.loads(config.read_text(encoding="utf-8"))
    del data["dataset"]
    config.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(KeyError, match="dataset"):
        run(tmp_path, config=config)


def test_missing_input_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Input tidak ditemukan"):
        run(tmp_path)


def test_empty_input_file_is_rejected(tmp_path: Path) -> None:
    write_input(tmp_path, "2024-01", payload=b"")

    with pytest.raises(ValueError, match="File kosong"):
        run(tmp_path)


def test_input_file_without_rows_is_rejected(tmp_path: Path) -> None:
    write_input(tmp_path, "2024-01")

    with pytest.raises(ValueError, match="File tidak berisi baris"):
        run(tmp_path, rows=0)

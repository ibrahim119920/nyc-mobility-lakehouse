"""Helpers that execute a Databricks notebook outside the Databricks runtime.

The notebooks rely on two objects provided by the platform: ``dbutils`` and
``spark``. Both are replaced with small stubs here so the real notebook source
is executed unchanged.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = REPO_ROOT / "notebooks"


class FakeWidgets:
    def __init__(self, values: dict[str, str] | None = None) -> None:
        self._values: dict[str, str] = dict(values or {})

    def text(self, name: str, default: str = "") -> None:
        self._values.setdefault(name, default)

    def get(self, name: str) -> str:
        return self._values[name]


class FakeTaskValues:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    def set(self, key: str, value: object) -> None:
        self.values[key] = value


class FakeJobs:
    def __init__(self) -> None:
        self.taskValues = FakeTaskValues()


class FakeDbutils:
    def __init__(self, values: dict[str, str] | None = None) -> None:
        self.widgets = FakeWidgets(values)
        self.jobs = FakeJobs()


class FakeParquet:
    def __init__(self, rows: int) -> None:
        self._rows = rows

    def limit(self, _count: int) -> FakeParquet:
        return self

    def count(self) -> int:
        return self._rows


class FakeReader:
    def __init__(self, rows: int) -> None:
        self._rows = rows

    def parquet(self, _path: str) -> FakeParquet:
        return FakeParquet(self._rows)


class FakeSpark:
    def __init__(self, rows: int = 1) -> None:
        self.read = FakeReader(rows)


def run_notebook(
    name: str,
    *,
    values: dict[str, str] | None = None,
    rows: int = 1,
) -> tuple[FakeDbutils, dict[str, object]]:
    """Execute a notebook file and return its stubbed ``dbutils`` and globals."""

    source = (NOTEBOOKS / name).read_text(encoding="utf-8")
    dbutils = FakeDbutils(values)
    namespace: dict[str, object] = {
        "__name__": "__notebook__",
        "dbutils": dbutils,
        "spark": FakeSpark(rows),
    }
    exec(compile(source, str(NOTEBOOKS / name), "exec"), namespace)
    return dbutils, namespace

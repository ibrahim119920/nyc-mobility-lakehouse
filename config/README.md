# Configuration

`batch.example.json` is a sample without credentials. Copy it to `batch.local.json` — which is git-ignored — and adjust the catalog, schema, and Volume names for your own workspace.

| Field | Responsibility |
| --- | --- |
| `dataset` | `yellow` only in this project. |
| `catalog`, `schema` | Namespace for the three Delta tables. |
| `raw_root` | Parent folder of the monthly files in the Unity Catalog Volume. |
| `tables` | Names of the Bronze, Silver, and Gold tables. |

The example uses the names from this project (`workspace`, `nyc_mobility`, `/Volumes/workspace/nyc_mobility/raw/yellow`). The input path is built as
`{raw_root}/{source_month}/{dataset}_tripdata_{source_month}.parquet`, so the file name must follow the TLC convention exactly.

`source_month` is passed as a workflow parameter, not stored as a fixed value in the configuration. `config_path` is the path to the JSON file in the workspace that Python can read from every task, for example
`/Workspace/Users/<email>/nyc-mobility-lakehouse/config/batch.local.json`.

`00_prepare_batch` reads the JSON and fails with a `KeyError` if one of `dataset`, `catalog`, `schema`, `raw_root`, or `tables` is missing; the other notebooks assume those keys exist.

Do not store PATs, passwords, or connection strings in this file. Use workspace authentication or Databricks secrets when a secret is needed.

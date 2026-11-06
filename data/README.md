# Dataset and downloads

Source: [NYC TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page).
Use **Yellow Taxi Trip Records** in Parquet format, one file per month. The
project started with January and February 2024 and was later backfilled to
September 2024, so nine monthly files were processed in total. The data
dictionary is available on the same TLC page; re-check the schema when
adding a new year/month.

## Manual download

1. Open the TLC page, select the year 2024.
2. Download Yellow Taxi for every month you want to process (January to September in this repo).
3. Save each file under the folder `data/raw/yellow/<YYYY-MM>/`.

Or run the following PowerShell from the repo root (downloads the raw files
locally):

```powershell
$months = @('2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06', '2024-07', '2024-08', '2024-09')
foreach ($month in $months) {
    $destinationDir = Join-Path 'data/raw/yellow' $month
    New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    $fileName = "yellow_tripdata_$month.parquet"
    $destinationFile = Join-Path $destinationDir $fileName
    if (-not (Test-Path -LiteralPath $destinationFile)) {
        $temporaryFile = "$destinationFile.download"
        Invoke-WebRequest -Uri "https://d37ci6vzurychx.cloudfront.net/trip-data/$fileName" -OutFile $temporaryFile
        Move-Item -LiteralPath $temporaryFile -Destination $destinationFile
    }
}
```

Use the links on the TLC page if the download URLs change. Verify that the file
is readable, its size/checksum, and its row count before processing.
The script skips files that already exist; replacing a corrected file must be
done deliberately.

## Layout in Databricks

Upload the downloaded files to a Unity Catalog Volume you set up yourself:

```text
/Volumes/<catalog>/<schema>/<volume>/raw/yellow/
├── 2024-01/yellow_tripdata_2024-01.parquet
├── 2024-02/yellow_tripdata_2024-02.parquet
├── ...
└── 2024-09/yellow_tripdata_2024-09.parquet
```

Set `raw_root` in the configuration to that `raw/yellow` directory. The
notebooks build the input path as
`{raw_root}/{source_month}/{dataset}_tripdata_{source_month}.parquet`, so the
folder and file names must match. Keep earlier monthly files when a new month is added.
One batch uses one complete monthly file, not partial chunks. Freeze the input
for the duration of a workflow.

The nine months processed here were loaded one month at a time through the same
job; see `evidence/day7/07-backfill.md` for the backfill and its preflight.

Do not commit raw datasets, transformation outputs, or credentials. The
`.gitignore` excludes everything in `data/` except this README. Small synthetic
fixtures are kept separately in `tests/fixtures/`. The taxi zone lookup can be
added later if analysis needs zone names; it is not required for the current
pipeline.

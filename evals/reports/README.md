# Eval Reports

Local run reports can live here when they are small and public-safe.

Large or repeated reports should be written to `CONNECTOR_ARTIFACT_ROOT` and
referenced by compact manifests.

The default `aoa-4pda eval search-quality` run prints a compact report to
stdout and deletes temporary indexes after the run. Do not commit repeated
generated reports unless they are intentionally curated examples.

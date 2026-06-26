# Eval Reports

Local run reports can live here when they are small and public-safe.

Large or repeated reports should be written to `CONNECTOR_ARTIFACT_ROOT` and
referenced by compact manifests.

The default `aoa-4pda eval search-quality` run prints a compact report to
stdout and deletes temporary indexes after the run. Do not commit repeated
generated reports unless they are intentionally curated examples.

Active local report notes:

- [connector-local-suite-route-pass-20260625.report.md](connector-local-suite-route-pass-20260625.report.md)
  records the current `aoa-eval-apply` route pass over connector-native
  offline/no-network suite runners.

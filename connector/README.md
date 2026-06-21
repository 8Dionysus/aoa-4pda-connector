# Connector Source Home

`connector/` holds source-owned connector contracts for 4PDA ingestion and
retrieval. It is the place to start when changing policy, profile shape,
schemas, seed routes, or fixture expectations.

## Folders

| Folder | Role |
| --- | --- |
| `profiles/` | bounded crawl/index build profiles |
| `seeds/` | small seed lists and seed-review manifests used by profiles |
| `manifests/` | connector metadata, artifact classes, route allowlist/denylist |
| `schemas/` | JSON schemas for normalized and generated packets |
| `fixtures/` | tiny synthetic examples safe for Git |
| `examples/` | query and evidence-packet examples |

## Rule

Keep this source home small and reproducible. Real captures, indexes, vectors,
graphs, and full exports belong in configured storage roots outside Git
history.

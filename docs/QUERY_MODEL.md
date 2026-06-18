# Query Model

The connector should answer through local evidence packets.

## Search Layers

- exact token search for device models, build IDs, versions, and error strings
- BM25 keyword search for public post text
- optional vector search for paraphrase recall
- entity search for devices, apps, firmware, versions, issues, fixes, warnings
- graph traversal for relations between topics, posts, fixes, and warnings

## Answer Contract

Every answer should carry:

- source URL
- topic id and post id when known
- observed/captured timestamps
- matched chunks or post refs
- freshness note
- policy route note


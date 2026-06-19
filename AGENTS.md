# AGENTS.md

Root route card for `aoa-4pda-connector`.

## Purpose

`aoa-4pda-connector` is an AoA external-source connector skeleton for building
local, policy-gated search and graph evidence from public 4PDA topic/post
pages.

The repository is GitHub-publishable method and code. It is not a corpus dump.

## Owner Lane

This repository owns:

- 4PDA connector source policy and route allowlist/denylist
- crawler, parser, normalizer, chunker, local index, graph, query, and export
  method skeletons
- evidence packet, normalized topic/post, index manifest, and graph schemas
- small synthetic fixtures, eval query seeds, and install/doctor routes
- validator checks that keep large generated data out of Git

It does not own:

- 4PDA content or platform policy
- private/account-gated data, QMS, login, usercp, post, attach, or download
  routes
- full raw captures, large indexes, graph databases, embeddings, or caches
- runtime/MCP deployment, which belongs in `abyss-stack`
- memory, proof, routing, or KAG doctrine owned by sibling AoA layers

## Start Here

1. `README.md`
2. `CHARTER.md`
3. `BOUNDARIES.md`
4. `connector/SOURCE_POLICY.md`
5. `connector/STORAGE_POLICY.md`
6. `docs/ARCHITECTURE.md`
7. `docs/INSTALL.md`
8. `docs/AGENT_INSTALL_ROUTE.md`
9. `docs/decisions/README.md`

Before large data, runtime, AI, or benchmark work, also read
`/etc/abyss-machine/AGENTS.md` and `/etc/abyss-machine/storage-policy.json`.

## Boundaries

- Do not run broad crawls unless the operator explicitly asks for a crawl.
- Do not download attachments.
- Do not call 4PDA internal search routes such as `act=search` or
  `act=Search`.
- Do not use login/private/QMS/usercp/post/attach/download routes.
- Do not bypass robots, account, privacy, or rate boundaries.
- Do not commit raw captures, indexes, graph DBs, vector stores, caches, or
  full exports.
- The repo-local `.connector-state/` directory is an ignored workspace for
  small starter runs. Treat generated files inside it as local state, not source
  truth.

## Validation

Run from the repository root:

```bash
python scripts/validate_connector.py
python -m pytest -q
```

The validator must stay safe on a fresh clone with no external storage mounted.

## Closeout

Report changed surfaces, validation results, skipped live crawl or storage
checks, and the next safe step. For this skeleton, the first safe materialized
step is `aoa-4pda materialize fixture`; the next network step is a starter
crawl over 10-30 public topic pages after policy and storage roots are
confirmed.

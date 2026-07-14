# Boundaries

This file names what belongs in `aoa-4pda-connector` and what must stay
elsewhere.

## Belongs Here

- source policy and robots-aware route constraints
- crawler, parser, normalizer, chunker, index, graph, query, and export code
- schemas for normalized posts, topics, graph nodes/edges, index manifests, and
  evidence packets
- small synthetic fixtures and expected packets
- starter seed lists and bounded crawl profiles
- connector-local information-need definitions and a root `stats/` port over
  their declared eval-route coverage
- install, agent-install, operations, and external-storage documentation
- validators that keep the repository GitHub-publishable

## Belongs Elsewhere

- raw public captures: external `CONNECTOR_DATA_ROOT`
- generated BM25/vector/entity indexes: external `CONNECTOR_CACHE_ROOT`
- graph databases and export artifacts: external `CONNECTOR_ARTIFACT_ROOT`
- runtime services and MCP adapters: `abyss-stack`
- host storage policy: `abyss-machine`
- shared stats grammar: `aoa-stats`
- proof, memory, routing, KAG, or playbook doctrine: owning AoA repositories

## Search Boundary

Do not use 4PDA internal search as source data or crawler API. The connector
builds its own local deep search from allowed public topic/post pages.

## Privacy and Policy Boundary

Do not access, infer, or store private/account-gated data. Do not bypass access
controls. Do not download attachments.

## Git Boundary

The repository must remain forkable. Large mutable data must stay ignored and
outside Git.

## Stats Boundary

The local stats port may count connector-authored profile, matrix, and suite
route declarations. It does not execute evals, accept verdicts, inspect raw
captures, infer freshness, or claim connector readiness. The reference packet
is a derived public snapshot and remains weaker than its owner sources.

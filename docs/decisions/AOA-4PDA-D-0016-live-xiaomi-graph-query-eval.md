# AOA-4PDA-D-0016: Live Xiaomi Graph Query Eval

## Status

Accepted.

## Context

The Xiaomi 13T profile now extracts root and recovery actions and builds graph
relation edges for target image files, tools, and firmware context. The
public-safe fixture suite proves the method on a tiny committed sample, but it
does not prove that graph context survives through local `query-graph` packets
over an operator-materialized live run.

The repository must remain GitHub-publishable. It can define the live gate and
small expectations, but live corpora, keyword indexes, and graph exports must
stay in configured storage.

## Decision

Add `aoa-4pda eval live-graph-query-quality` and the focused suite
`evals/suites/live_xiaomi_13t_graph_query_quality.json`.

The eval reads existing configured-storage receipts for a named run:

- crawl receipt
- normalize receipt
- keyword index receipt
- graph receipt

It then runs local `query-graph` packets and checks that:

- crawl policy remains public-topic-only with no internal search or
  attachments
- the run matches the expected `xiaomi-13t` profile
- keyword index and graph artifacts are present
- only the original crawl stage touched the network
- root/recovery relation context is present in cited top results

The suite is intentionally receipt-driven. It does not crawl, rebuild a corpus,
use 4PDA internal search, or commit generated artifacts.

## Consequences

Agents can now verify Xiaomi 13T graph-query behavior against a real bounded
local corpus without confusing generated state with source truth.

The eval is still local connector evidence, not a central `aoa-evals` verdict.
It is tied to an operator-materialized run and should be refreshed when the
focused Xiaomi corpus or extraction semantics change.

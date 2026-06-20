# AOA-4PDA-D-0015: Xiaomi Entity Extraction V2

## Status

Accepted.

## Context

The Xiaomi 13T focused profile needs deeper local search than top-level topic
matching. Public firmware posts often encode useful evidence as dense technical
phrases: model numbers, device codenames, HyperOS versions, image file names,
root instructions, recovery flashing steps, and tool names. Those details must
be indexed and connected locally so agents can find and traverse them without
using 4PDA internal search.

The repository must remain public and portable. It can carry method, schemas,
small sanitized fixtures, and eval suites, but not large generated indexes or
full forum corpora.

## Decision

Extend heuristic entity extraction with a focused Xiaomi firmware/root/recovery
slice:

- device model numbers such as `2306EPN60G`
- Xiaomi 13T codename evidence such as `aristotle`
- HyperOS and OS build/version strings
- image files such as `boot.img`, `vendor_boot-aristotle.img`, and
  `recovery.img`
- root actions such as `patch boot.img`
- recovery actions such as `flash recovery.img`
- tools such as Magisk, KSU, TWRP, OrangeFox, and fastboot

Add graph relation edges that connect root and recovery actions to their local
post evidence:

- root action -> target image file
- root action -> tool
- root action -> firmware context
- recovery action -> target image file
- recovery action -> tool
- recovery action -> firmware context

Protect this route with a small public-safe fixture and
`evals/suites/xiaomi_13t_graph_relations.json`. Generated indexes and graph
exports remain ignored runtime artifacts in configured storage roots.

## Consequences

The connector gains a more useful graph navigation surface for Xiaomi 13T
firmware/root/recovery queries while keeping the proof route small enough for a
public repository.

The new relations are still heuristic navigation hints. They inherit cited
post source refs and confidence values; they are not central proof verdicts and
do not claim that an instruction is universally safe for every firmware build.

The same pattern can later be repeated for XDA, Telegram, Stack Overflow,
Discord, and other connector repos: keep method and small eval fixtures in Git,
keep large mutable indexes and graphs in configured storage, and make each
connector's focused extraction rules explicit and testable.

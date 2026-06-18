# Source Policy

This policy keeps the connector inside public, respectful, reproducible
source-intake boundaries.

## Allowed Source Shape

- public 4PDA topic pages and their public post pages
- bounded starter topic lists chosen by the operator
- source URLs preserved in every normalized topic, post, chunk, graph node, and
  evidence packet

## Forbidden Routes

The connector must not call internal or service routes as source data or crawler
APIs, including:

- internal search: `act=search`, `act=Search`
- login/auth/user routes: `act=login`, `act=Login`, `act=auth`, `act=usercp`
- write/moderation routes: `act=post`, `act=Post`, `act=report`, `act=warn`
- attachment/download routes: `act=attach`, `/forum/dl`
- private/account-gated data, QMS, or any route requiring credentials
- bypasses, scraping around access controls, or load-heavy enumeration

## Search Model

Do not use 4PDA internal search as a crawler API. Build local deep search from
allowed public topic/post snapshots:

```text
allowed public topic pages
-> normalized topic/post records
-> local chunks and entity refs
-> local BM25/vector/entity/graph indexes
-> evidence packets with source URLs
```

## Crawl Posture

- default to no network work
- require explicit operator intent for any crawl
- use bounded profiles
- keep rate limits conservative
- persist crawl receipts
- retry politely and stop on policy uncertainty

## Citation and Freshness

Every answer path should return evidence, not just extracted text:

- source URL
- topic id and post id when known
- observed timestamp
- capture timestamp
- profile/run id
- freshness and confidence notes


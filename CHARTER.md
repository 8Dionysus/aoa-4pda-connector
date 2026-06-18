# Charter

`aoa-4pda-connector` exists to make public 4PDA knowledge retrievable through a
reproducible, source-linked, policy-gated local connector.

## Mission

The connector should let an operator or agent install the repository, configure
external storage, collect a bounded public topic corpus, normalize posts, build
local search and graph indexes, and answer with evidence packets that link back
to public source URLs.

## Owns

- connector-specific source policy and route allowlists
- reproducible install and doctor route
- safe crawler/parser/normalizer/index/graph/query skeletons
- schemas and small fixtures for evidence packets
- local validation that prevents heavy artifacts from entering Git

## Does Not Own

- 4PDA's content, service policy, accounts, or private areas
- login, post, user control, QMS, attachment, download, or internal search
  routes
- large generated corpora, indexes, graph databases, vector stores, or caches
- runtime access-plane deployment

## Principle

Git stores the method. External storage carries the mass.


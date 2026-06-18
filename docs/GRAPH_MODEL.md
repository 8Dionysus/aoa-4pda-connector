# Graph Model

The graph is a derived navigation layer, not source truth.

## Node Kinds

- `forum`
- `topic`
- `post`
- `header_post`
- `device`
- `codename`
- `firmware_family`
- `firmware_version`
- `build_id`
- `tool`
- `file`
- `issue`
- `fix`
- `warning`
- `external_link`

Entity node ids are scoped by kind: `entity:<kind>:<value>`. This avoids
collapsing different facts that happen to share similar values.

## Edge Kinds

- `topic_contains_post`
- `post_mentions_entity`
- `topic_about_device`
- `fixes_issue`
- `warns_about`
- `supersedes`
- `quotes`
- `same_device_alias`

## Evidence

Every node or edge derived from content must include source refs and confidence.

## Starter Entity Extraction

Entity extraction v1 is heuristic and local:

- regexes for firmware versions, build IDs, files, and common device names
- small dictionaries for tools, firmware families, known codenames, and common
  issue words
- bounded fix/warning patterns around technical files such as `boot.img`

It is a navigation layer, not a final classifier.

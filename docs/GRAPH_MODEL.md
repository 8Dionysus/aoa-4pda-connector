# Graph Model

The graph is a derived navigation layer, not source truth.

## Node Kinds

- `forum`
- `topic`
- `post`
- `header_post`
- `device`
- `firmware`
- `app`
- `version`
- `issue`
- `fix`
- `warning`
- `external_link`

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


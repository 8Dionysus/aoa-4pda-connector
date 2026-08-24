# Releasing `aoa-4pda-connector`

This repository is an independently publishable connector, but it is not in
the `aoa-sdk` `OWNER_RELEASE_REPOS` federation. Its release authority is
therefore this owner-local route plus GitHub's repository release API. The
generic `aoa release` command must not be used as a substitute for this
contract: it intentionally rejects this repository as an unknown owner.

## Release identity

- The consolidated source release is `0.1.0` / `v0.1.0`. It is the only
  campaign release after cleanup, and its existing tag/Release is the sole
  final publication. The four same-day pre-cleanup Release/tag carriers and
  their source material remain recorded as historical evidence in the
  task-local conservation ledger.
- This source and publication line includes one explicitly authorized,
  target-only post-audit reconsolidation. Before changing the existing
  `v0.1.0` identity, the owner must capture a digest-bound snapshot of its tag
  object, peeled commit, Release, body, assets, tagged changelog, deleted
  carriers, and conservation ledger. The owner may then delete and recreate
  only the `v0.1.0` tag ref at the exact landed `main` commit and update only
  the existing `v0.1.0` Release body. No second Release, version, tag, or
  sibling repository is in scope; this is not general overwrite authority.
- `pyproject.toml`, `src/aoa_4pda_connector/__init__.py`, the connector
  manifest, the README marker, and the dated `CHANGELOG.md` heading must agree.
- `connector-ready-v1` remains an independent maturity target. A release does
  not change `status: skeleton`, `ready=false`, or the runtime/MCP ownership
  boundary.
- A release is source-only unless a separately admitted artifact class and
  public asset attestation exist. This repository currently has no
  `abyss-machine` artifact-policy class, registry producer, or public asset
  route of its own. Do not borrow a sibling class.

## Provider-before-consumer preflight

The release candidate requires these exact published provider tags:

| Provider | Required tag | Consumer pin in `.github/workflows/validate.yml` | Requirement |
| --- | --- | --- | --- |
| `8Dionysus/aoa-kag` | `v0.5.0` | action `f46f146cc79a26fa81ad0f400b9c5774df293e57`; owner-family/generated pin `f46f146cc79a26fa81ad0f400b9c5774df293e57` | `v0.5.0` tag object `8f63e3ae558ea96d21ee06becfa6ef61d63d698a` peels to `f46f146cc79a26fa81ad0f400b9c5774df293e57`; ancestor-only action/family pins are invalid |
| `8Dionysus/aoa-stats` | `v0.2.0` | `AOA_STATS_REVISION=88ff38b1b38eef939f2c5b4541cbe8363a05fc8d` | tag object `a63dd6f95c6f0c87a371720885c2d90a1baa3436` peels to `88ff38b1b38eef939f2c5b4541cbe8363a05fc8d`; the workflow checkout must equal the published tag's peeled commit |

The direct `aoa-stats` body-provider pin is an immutable identity, not an
ancestor constraint. A green `git merge-base --is-ancestor` result for an
older stats commit is insufficient and must fail the release route. The
release executor must re-check the GitHub Release, tag object, peeled commit,
and exact direct-provider pin immediately before the PR and again before
publish. The check is evidence, not a claim that a provider runtime is
healthy.

## Required checks

From a clean release-prep worktree run `python scripts/release_check.py
--version 0.1.0`, `python scripts/validate_connector.py`, `python
scripts/validate_local_stats_port.py`, `python -m pytest -q -p
no:cacheprovider`, `python -m compileall -q src scripts`, and the two
no-network CLI routes `PYTHONPATH=src python -m aoa_4pda_connector.cli doctor`
and `PYTHONPATH=src python -m aoa_4pda_connector.cli ready`.

The `ready` result is recorded honestly. It is not a release pass/fail proxy
and it must not be upgraded by publication.

The exact published `aoa-kag@v0.5.0` owner generator
`scripts/generate_repo_local_kag_index.py` must check
`kag/indexes/source_surface_index.json` with `--portable-family --check`; its
`scripts/validate_repo_local_kag_family.py` must then validate the same repo
root. These scripts are run from the pinned provider checkout because this
connector intentionally does not copy sibling owner tools into its source.

The source owner must regenerate the family with the exact published
`aoa-kag@v0.5.0` provider when source/docs/decision surfaces change. Generated
indexes are consumer-visible derived read models, not authority over the
authored docs or release decision.

## Artifact and attestation boundary

Run `abyss-machine artifacts requirements --json` and retain the host policy
inventory result in the release report.

For this source-only release, the expected result is no connector-owned
artifact class and no public asset to admit. A Python wheel/sdist may be
built as local validation evidence, but it must not be described as a trusted
public release artifact without an owner class, required sidecars, admission,
and a public attestation. The GitHub Release itself is publication evidence,
not an artifact trust receipt or runtime proof.

## Publication sequence

1. Build and validate on a PR branch based on current `origin/main`.
2. Re-check both provider Releases/tags and the exact direct stats pin; create
   a release-prep PR.
3. Wait for the required `Validate` check, repair failures, and merge through
   GitHub using squash.
4. Sync local `main` to the exact landed commit and repeat the full gates.
5. Run the owner-local dry-run with `python scripts/release_publish.py
   --version 0.1.0 --tag v0.1.0 --dry-run`. Because the target already exists,
   the standard publisher is expected to refuse mutation; that refusal is
   evidence that the ordinary route is fail-closed, not a reason to create a
   corrective version.

6. For this one-time authorized reconsolidation, after the pre-mutation
   snapshot and exact-landed gates pass, delete and recreate only the
   `refs/tags/v0.1.0` annotated tag at landed `main`, then PATCH the existing
   Release `v0.1.0` body from the canonical dated changelog section. Preserve
   its stable/non-draft/non-prerelease flags and zero-asset state; verify that
   no other tag or Release changed and that the release inventory still has
   exactly one campaign entry. The normal publisher's overwrite refusal
   remains in force for every other release operation.

The publisher refuses to overwrite an existing tag or release, requires a
clean `main` at the local `origin/main`, creates an annotated tag at that
exact commit, publishes the canonical changelog section, and verifies tag
identity, release body, stable latest marker, and asset state afterward.

## Rollback and non-claims

The standard publisher has no force-tag, delete-release, or overwrite path.
The single target-only reconsolidation above is an explicit, audited exception
for this campaign and must never be generalized to another tag or Release.
The release does not prove source deployment, runtime activation, runtime
health, corpus completeness, semantic answer quality, central proof, or human
acceptance.

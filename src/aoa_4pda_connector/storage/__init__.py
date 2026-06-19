"""Configured storage route helpers."""

from __future__ import annotations

from pathlib import Path

from aoa_4pda_connector.config import LOCAL_STATE_DIR, StorageRoots, path_is_inside


def storage_warnings(repo_root: Path, roots: StorageRoots | None = None) -> list[str]:
    roots = roots or StorageRoots.from_env(repo_root)
    local_state_root = repo_root / LOCAL_STATE_DIR
    warnings: list[str] = []
    for name, value in roots.as_dict().items():
        if value is None:
            warnings.append(f"{name} is not set")
            continue
        path = Path(value)
        if path_is_inside(path, repo_root) and not path_is_inside(path, local_state_root):
            warnings.append(f"{name} points inside the repository: {path}")
    return warnings


def create_storage_roots(roots: StorageRoots) -> list[str]:
    created: list[str] = []
    for path in [roots.data, roots.cache, roots.artifact]:
        if path is None:
            continue
        path.mkdir(parents=True, exist_ok=True)
        created.append(str(path))
    return created

from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ROOT / "services/api/migrations/versions"
ENV_PATH = ROOT / "services/api/migrations/env.py"
INI_PATH = ROOT / "services/api/alembic.ini"
EXPECTED_ROOT = "20260727_0001"
EXPECTED_HEAD = "20260806_0034"
EXPECTED_COUNT = 34


def _literal_assignment(tree: ast.Module, name: str):
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                value = node.value
                return ast.literal_eval(value)
    raise AssertionError(f"missing {name} assignment")


def _load_chain() -> tuple[dict[str, str | None], str]:
    files = sorted(VERSIONS.glob("*.py"))
    assert len(files) == EXPECTED_COUNT, (
        f"expected {EXPECTED_COUNT} migration files, found {len(files)}"
    )

    parents: dict[str, str | None] = {}
    source_digest = hashlib.sha256()
    for path in files:
        source = path.read_text(encoding="utf-8")
        source_digest.update(path.name.encode("utf-8"))
        source_digest.update(b"\0")
        source_digest.update(source.encode("utf-8"))
        tree = ast.parse(source, filename=str(path))
        revision = _literal_assignment(tree, "revision")
        down_revision = _literal_assignment(tree, "down_revision")
        assert isinstance(revision, str), f"{path.name}: revision must be a string"
        assert down_revision is None or isinstance(down_revision, str), (
            f"{path.name}: merge/branch down_revision is not allowed"
        )
        assert revision not in parents, f"duplicate revision {revision}"
        assert path.name.startswith(revision), (
            f"{path.name}: filename must start with revision {revision}"
        )
        parents[revision] = down_revision

    roots = [revision for revision, parent in parents.items() if parent is None]
    referenced = {parent for parent in parents.values() if parent is not None}
    heads = [revision for revision in parents if revision not in referenced]
    assert roots == [EXPECTED_ROOT], f"expected root {EXPECTED_ROOT}, got {roots}"
    assert heads == [EXPECTED_HEAD], f"expected head {EXPECTED_HEAD}, got {heads}"

    current = EXPECTED_HEAD
    visited: list[str] = []
    while current is not None:
        assert current not in visited, f"cycle detected at {current}"
        assert current in parents, f"missing parent revision {current}"
        visited.append(current)
        current = parents[current]

    assert len(visited) == EXPECTED_COUNT, (
        f"head-to-root chain contains {len(visited)} revisions; expected {EXPECTED_COUNT}"
    )
    assert visited[-1] == EXPECTED_ROOT
    assert set(visited) == set(parents), "disconnected migration revision detected"
    return parents, source_digest.hexdigest()


def _validate_offline_boundary() -> None:
    env_text = ENV_PATH.read_text(encoding="utf-8")
    ini_text = INI_PATH.read_text(encoding="utf-8")
    assert "context.is_offline_mode()" in env_text
    assert "literal_binds=True" in env_text
    assert "script_location = migrations" in ini_text
    assert "sqlalchemy.url = postgresql+psycopg://" in ini_text


def _validate_snapshot(path: Path) -> str:
    data = path.read_bytes()
    assert len(data) > 4096, "generated schema snapshot is unexpectedly small"
    text = data.decode("utf-8")
    assert "alembic_version" in text, "snapshot lacks Alembic version tracking"
    assert EXPECTED_HEAD in text, "snapshot does not reach the canonical Alembic head"
    assert "schema.invalid" not in text, "placeholder connection host leaked into SQL"
    assert "postgresql+psycopg://" not in text, "connection string leaked into SQL"
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()

    _, source_digest = _load_chain()
    _validate_offline_boundary()
    print(f"canonical_migration_count={EXPECTED_COUNT}")
    print(f"canonical_root={EXPECTED_ROOT}")
    print(f"canonical_head={EXPECTED_HEAD}")
    print(f"migration_source_sha256={source_digest}")

    if args.snapshot is not None:
        snapshot_digest = _validate_snapshot(args.snapshot)
        print(f"snapshot_sha256={snapshot_digest}")


if __name__ == "__main__":
    main()

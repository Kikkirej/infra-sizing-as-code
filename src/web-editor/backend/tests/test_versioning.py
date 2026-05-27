"""Tests for versioning endpoints (US1–US4)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.state import ChangeState, EditorState, UnitsNode
from services import state_store


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def repo_root(tmp_path):
    """Minimal repo root with one product."""
    infra = tmp_path / "infra"
    product_dir = infra / "acme-test"
    product_dir.mkdir(parents=True)
    (tmp_path / "infra" / "products.json").write_text(
        json.dumps([{"shortname": "acme-test", "display_name": "Acme Test"}])
    )
    (product_dir / "meta.json").write_text(json.dumps({"prefix": "prefix.adoc", "suffix": "suffix.adoc"}))
    (product_dir / "prefix.adoc").write_text("")
    (product_dir / "suffix.adoc").write_text("")
    return tmp_path


@pytest.fixture
def client(repo_root, monkeypatch):
    import routers.versioning as vmod
    import routers.git as gmod
    monkeypatch.setattr(vmod, "REPO_ROOT", repo_root)
    monkeypatch.setattr(gmod, "REPO_ROOT", repo_root)
    state_store._state = EditorState(
        units=UnitsNode(units=["vCPU", "GB"], change=ChangeState.CLEAN),
    )
    from main import app
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def wip_path(repo_root):
    vdir = repo_root / "infra" / "acme-test" / "versioning"
    vdir.mkdir(parents=True, exist_ok=True)
    return vdir / "wip.json"


def write_wip(wip_path, version_name="1.0.0", entries=None):
    if entries is None:
        entries = [{"author": "Jane, Smith", "date": "2026-05-26", "notes": "Init"}]
    wip_path.write_text(json.dumps({"version_name": version_name, "entries": entries}))


# ── US1: list & get versions ─────────────────────────────────────────────────

def test_list_versions_no_dir(client):
    r = client.get("/api/products/acme-test/versioning")
    assert r.status_code == 200
    assert r.json() == {"wip": False, "versions": []}


def test_list_versions_with_wip(client, wip_path):
    write_wip(wip_path)
    r = client.get("/api/products/acme-test/versioning")
    assert r.status_code == 200
    data = r.json()
    assert data["wip"] is True
    assert data["versions"] == []


def test_list_versions_with_released(client, wip_path):
    write_wip(wip_path)
    released = wip_path.parent / "1.0.0.json"
    released.write_text(json.dumps({"version_name": "1.0.0", "entries": []}))
    r = client.get("/api/products/acme-test/versioning")
    data = r.json()
    assert data["wip"] is True
    assert "1.0.0" in data["versions"]


def test_list_versions_unknown_product(client):
    r = client.get("/api/products/no-such/versioning")
    assert r.status_code == 404


def test_get_wip_missing(client):
    r = client.get("/api/products/acme-test/versioning/wip")
    assert r.status_code == 200
    assert r.json()["entries"] == []
    assert r.json()["readonly"] is False


def test_get_wip(client, wip_path):
    write_wip(wip_path)
    r = client.get("/api/products/acme-test/versioning/wip")
    assert r.status_code == 200
    data = r.json()
    assert data["version_name"] == "1.0.0"
    assert len(data["entries"]) == 1
    assert data["readonly"] is False


def test_get_wip_malformed(client, wip_path):
    wip_path.parent.mkdir(parents=True, exist_ok=True)
    wip_path.write_text("not json{{{")
    r = client.get("/api/products/acme-test/versioning/wip")
    assert r.status_code == 422


def test_get_released_version(client, wip_path):
    write_wip(wip_path)
    released = wip_path.parent / "0.9.0.json"
    released.write_text(json.dumps({"version_name": "0.9.0", "entries": [{"author": "John, Doe", "date": "2026-01-01", "notes": None}]}))
    r = client.get("/api/products/acme-test/versioning/0.9.0")
    assert r.status_code == 200
    assert r.json()["readonly"] is True


def test_get_version_not_found(client):
    r = client.get("/api/products/acme-test/versioning/9.9.9")
    assert r.status_code == 404


# ── US1: reset malformed WIP ─────────────────────────────────────────────────

def test_reset_wip(client, wip_path):
    wip_path.parent.mkdir(parents=True, exist_ok=True)
    wip_path.write_text("invalid")
    r = client.post("/api/products/acme-test/versioning/wip/reset")
    assert r.status_code == 200
    assert r.json()["entries"] == []
    assert r.json()["readonly"] is False
    assert json.loads(wip_path.read_text()) == {"version_name": "", "entries": []}


# ── US2: version_name update ─────────────────────────────────────────────────

def test_patch_version_name(client, wip_path):
    write_wip(wip_path)
    r = client.patch("/api/products/acme-test/versioning/wip", json={"version_name": "1.1.0"})
    assert r.status_code == 200
    assert r.json()["version_name"] == "1.1.0"
    assert json.loads(wip_path.read_text())["version_name"] == "1.1.0"


def test_patch_version_name_invalid_chars(client, wip_path):
    write_wip(wip_path)
    r = client.patch("/api/products/acme-test/versioning/wip", json={"version_name": "1.1 0"})
    assert r.status_code == 422


# ── US2: entry CRUD ───────────────────────────────────────────────────────────

def test_create_entry_valid(client, wip_path):
    write_wip(wip_path, entries=[])
    r = client.post(
        "/api/products/acme-test/versioning/wip/entries",
        json={"author": "Jane, Smith", "date": "2026-05-26", "notes": "first"},
    )
    assert r.status_code == 201
    data = json.loads(wip_path.read_text())
    assert len(data["entries"]) == 1


def test_create_entry_multi_author_valid(client, wip_path):
    write_wip(wip_path, entries=[])
    r = client.post(
        "/api/products/acme-test/versioning/wip/entries",
        json={"author": "Jane, Smith; John, Doe", "date": "2026-05-26"},
    )
    assert r.status_code == 201


def test_create_entry_invalid_author(client, wip_path):
    write_wip(wip_path, entries=[])
    r = client.post(
        "/api/products/acme-test/versioning/wip/entries",
        json={"author": "JohnDoe", "date": "2026-05-26"},
    )
    assert r.status_code == 422
    assert "JohnDoe" in str(r.json()["detail"])


def test_create_entry_mixed_invalid_authors(client, wip_path):
    write_wip(wip_path, entries=[])
    r = client.post(
        "/api/products/acme-test/versioning/wip/entries",
        json={"author": "Jane, Smith; JohnDoe; Jane", "date": "2026-05-26"},
    )
    assert r.status_code == 422
    detail = str(r.json()["detail"])
    assert "JohnDoe" in detail
    assert "Jane" in detail


def test_update_entry(client, wip_path):
    write_wip(wip_path)
    r = client.put(
        "/api/products/acme-test/versioning/wip/entries/0",
        json={"author": "John, Doe", "date": "2026-05-27", "notes": "updated"},
    )
    assert r.status_code == 200
    data = json.loads(wip_path.read_text())
    assert data["entries"][0]["author"] == "John, Doe"


def test_update_entry_out_of_range(client, wip_path):
    write_wip(wip_path)
    r = client.put(
        "/api/products/acme-test/versioning/wip/entries/99",
        json={"author": "John, Doe", "date": "2026-05-27"},
    )
    assert r.status_code == 404


def test_delete_entry(client, wip_path):
    write_wip(wip_path)
    r = client.delete("/api/products/acme-test/versioning/wip/entries/0")
    assert r.status_code == 200
    data = json.loads(wip_path.read_text())
    assert data["entries"] == []


def test_delete_entry_out_of_range(client, wip_path):
    write_wip(wip_path)
    r = client.delete("/api/products/acme-test/versioning/wip/entries/99")
    assert r.status_code == 404


# ── US3: release ─────────────────────────────────────────────────────────────

def test_release_happy_path(client, wip_path, repo_root, monkeypatch):
    write_wip(wip_path)
    import routers.versioning as vmod
    # Patch git operations
    class FakeTag:
        pass
    class FakeCommit:
        hexsha = "abc1234567"
    class FakeIndex:
        def commit(self, msg):
            return FakeCommit()
    class FakeGit:
        def add(self, **kwargs):
            pass
    class FakeRepo:
        git = FakeGit()
        index = FakeIndex()
        def create_tag(self, name):
            pass
    monkeypatch.setattr("routers.versioning.REPO_ROOT", repo_root)
    import unittest.mock as mock
    with mock.patch("git.Repo", return_value=FakeRepo()):
        r = client.post(
            "/api/products/acme-test/release",
            json={"new_version_name": "1.1.0"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["version_name"] == "1.0.0"
    assert data["tag"] == "acme-test-1.0.0"
    assert data["new_wip_version_name"] == "1.1.0"
    # Released file created
    assert (wip_path.parent / "1.0.0.json").exists()
    # New wip.json seeded
    new_wip = json.loads(wip_path.read_text())
    assert new_wip["version_name"] == "1.1.0"
    assert new_wip["entries"][0]["notes"] == "copied from previous version"
    assert new_wip["entries"][0]["author"] == "Jane, Smith"


def test_release_empty_wip_blocked(client, wip_path):
    write_wip(wip_path, entries=[])
    r = client.post("/api/products/acme-test/release", json={"new_version_name": "1.1.0"})
    assert r.status_code == 422
    assert "no change entries" in r.json()["detail"]


def test_release_duplicate_version_blocked(client, wip_path):
    write_wip(wip_path)
    released = wip_path.parent / "1.0.0.json"
    released.write_text(json.dumps({"version_name": "1.0.0", "entries": []}))
    import unittest.mock as mock
    with mock.patch("git.Repo"):
        r = client.post("/api/products/acme-test/release", json={"new_version_name": "1.1.0"})
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"]


def test_release_invalid_version_name(client, wip_path):
    write_wip(wip_path, version_name="bad name!")
    r = client.post("/api/products/acme-test/release", json={"new_version_name": "1.1.0"})
    assert r.status_code == 422


def test_release_invalid_new_version_name(client, wip_path):
    write_wip(wip_path)
    r = client.post("/api/products/acme-test/release", json={"new_version_name": "bad name!"})
    assert r.status_code == 422


def test_release_malformed_wip(client, wip_path):
    wip_path.parent.mkdir(parents=True, exist_ok=True)
    wip_path.write_text("not json")
    r = client.post("/api/products/acme-test/release", json={"new_version_name": "1.1.0"})
    assert r.status_code == 422


# ── US4: commit with version notes ───────────────────────────────────────────

def test_commit_with_valid_version_note(client, wip_path, repo_root, monkeypatch):
    write_wip(wip_path)
    import routers.git as gmod
    monkeypatch.setattr(gmod, "REPO_ROOT", repo_root)

    class FakeCommit:
        hexsha = "def456789a"
    class FakeIndex:
        def commit(self, msg):
            return FakeCommit()
    class FakeGit:
        def add(self, **kwargs):
            pass
        def execute(self, *a, **kw):
            pass
    class FakeRemote:
        def push(self):
            pass
    class FakeRepo:
        git = FakeGit()
        index = FakeIndex()
        remotes = []
        head = type("H", (), {"is_detached": False})()
        active_branch = type("B", (), {"name": "test"})()

    import unittest.mock as mock
    from services import writer
    with mock.patch("git.Repo", return_value=FakeRepo()):
        with mock.patch.object(writer, "write_all"):
            r = client.post("/api/git/commit", json={
                "message": "test commit",
                "push": False,
                "version_notes": [{
                    "product_shortname": "acme-test",
                    "author": "Jane, Smith",
                    "date": "2026-05-26",
                    "notes": "HA config added",
                }],
            })
    assert r.status_code == 200
    data = json.loads(wip_path.read_text())
    assert any(e["author"] == "Jane, Smith" and e["notes"] == "HA config added" for e in data["entries"])


def test_commit_invalid_version_note_blocks(client, wip_path):
    write_wip(wip_path)
    r = client.post("/api/git/commit", json={
        "message": "test",
        "push": False,
        "version_notes": [{
            "product_shortname": "acme-test",
            "author": "InvalidName",
            "date": "2026-05-26",
        }],
    })
    assert r.status_code == 422


def test_commit_empty_version_notes_ok(client, repo_root, monkeypatch):
    import routers.git as gmod
    monkeypatch.setattr(gmod, "REPO_ROOT", repo_root)

    class FakeCommit:
        hexsha = "aaa111222"
    class FakeIndex:
        def commit(self, msg):
            return FakeCommit()
    class FakeGit:
        def add(self, **kwargs):
            pass
    class FakeRepo:
        git = FakeGit()
        index = FakeIndex()
        remotes = []
        head = type("H", (), {"is_detached": False})()
        active_branch = type("B", (), {"name": "test"})()

    import unittest.mock as mock
    from services import writer
    with mock.patch("git.Repo", return_value=FakeRepo()):
        with mock.patch.object(writer, "write_all"):
            r = client.post("/api/git/commit", json={
                "message": "test commit",
                "push": False,
                "version_notes": [],
            })
    assert r.status_code == 200


def test_commit_version_note_creates_wip_if_missing(client, repo_root, monkeypatch):
    """Version note for a product with no existing versioning dir creates wip.json."""
    import routers.git as gmod
    monkeypatch.setattr(gmod, "REPO_ROOT", repo_root)

    class FakeCommit:
        hexsha = "bbb222333"
    class FakeIndex:
        def commit(self, msg):
            return FakeCommit()
    class FakeGit:
        def add(self, **kwargs):
            pass
    class FakeRepo:
        git = FakeGit()
        index = FakeIndex()
        remotes = []
        head = type("H", (), {"is_detached": False})()
        active_branch = type("B", (), {"name": "test"})()

    import unittest.mock as mock
    from services import writer
    with mock.patch("git.Repo", return_value=FakeRepo()):
        with mock.patch.object(writer, "write_all"):
            r = client.post("/api/git/commit", json={
                "message": "test commit",
                "push": False,
                "version_notes": [{
                    "product_shortname": "acme-test",
                    "author": "John, Doe",
                    "date": "2026-05-26",
                }],
            })
    assert r.status_code == 200
    wip = repo_root / "infra" / "acme-test" / "versioning" / "wip.json"
    assert wip.exists()
    data = json.loads(wip.read_text())
    assert data["entries"][0]["author"] == "John, Doe"

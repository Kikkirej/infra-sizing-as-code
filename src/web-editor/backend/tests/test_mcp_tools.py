from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent  # repo root


# ── Helpers ──────────────────────────────────────────────────────────────────

def _set_repo_root(monkeypatch, path: Path):
    import mcp_server.server as srv
    import mcp_server.reader as rdr
    monkeypatch.setattr(srv, "REPO_ROOT", path)
    monkeypatch.setattr(rdr, "__file__", rdr.__file__)  # no-op, just ensures module loaded


# ── US1: get_flavour_spec ────────────────────────────────────────────────────

def test_get_flavour_spec_valid(monkeypatch):
    import mcp_server.server as srv
    monkeypatch.setattr(srv, "REPO_ROOT", REPO_ROOT)

    result = json.loads(srv.get_flavour_spec("acme-crm", "small", "appserver"))

    assert result["shortname"] == "appserver"
    assert result["display_name"] == "Application Servers"
    servers = result["servers"]
    assert len(servers) >= 1
    first = servers[0]
    assert first["cpu"]["unit"] == "vCPU"
    assert first["memory"]["unit"] == "GB"
    assert isinstance(first["count"], int)


def test_get_flavour_spec_invalid_product(monkeypatch):
    import mcp_server.server as srv
    monkeypatch.setattr(srv, "REPO_ROOT", REPO_ROOT)

    result = srv.get_flavour_spec("no-such-product", "small", "appserver")

    assert "no-such-product" in result
    assert "not found" in result.lower()


def test_get_flavour_spec_invalid_size(monkeypatch):
    import mcp_server.server as srv
    monkeypatch.setattr(srv, "REPO_ROOT", REPO_ROOT)

    result = srv.get_flavour_spec("acme-crm", "no-such-size", "appserver")

    assert "no-such-size" in result
    assert "not found" in result.lower()


def test_get_flavour_spec_invalid_flavour(monkeypatch):
    import mcp_server.server as srv
    monkeypatch.setattr(srv, "REPO_ROOT", REPO_ROOT)

    result = srv.get_flavour_spec("acme-crm", "small", "no-such-flavour")

    assert "no-such-flavour" in result
    assert "not found" in result.lower()


# ── US2: list_products ───────────────────────────────────────────────────────

def test_list_products_returns_known_products(monkeypatch):
    import mcp_server.server as srv
    monkeypatch.setattr(srv, "REPO_ROOT", REPO_ROOT)

    result = json.loads(srv.list_products())

    shortnames = [p["shortname"] for p in result]
    assert "acme-crm" in shortnames
    assert "acme-erp" in shortnames
    assert len(result) >= 1
    assert all("shortname" in p and "display_name" in p for p in result)


def test_list_sizes_valid_product(monkeypatch):
    import mcp_server.server as srv
    monkeypatch.setattr(srv, "REPO_ROOT", REPO_ROOT)

    result = json.loads(srv.list_sizes("acme-crm"))

    shortnames = [s["shortname"] for s in result]
    assert "small" in shortnames
    assert "medium" in shortnames
    assert "large" in shortnames


def test_list_sizes_invalid_product(monkeypatch):
    import mcp_server.server as srv
    monkeypatch.setattr(srv, "REPO_ROOT", REPO_ROOT)

    result = srv.list_sizes("no-such-product")

    assert "no-such-product" in result
    assert "not found" in result.lower()


def test_list_flavours_valid(monkeypatch):
    import mcp_server.server as srv
    monkeypatch.setattr(srv, "REPO_ROOT", REPO_ROOT)

    result = json.loads(srv.list_flavours("acme-crm", "small"))

    shortnames = [f["shortname"] for f in result]
    assert "appserver" in shortnames
    assert "dbserver" in shortnames


def test_list_flavours_invalid_size(monkeypatch):
    import mcp_server.server as srv
    monkeypatch.setattr(srv, "REPO_ROOT", REPO_ROOT)

    result = srv.list_flavours("acme-crm", "no-such-size")

    assert "no-such-size" in result
    assert "not found" in result.lower()


# ── T012 cross-check: no editor fields in get_flavour_spec response ──────────

def test_get_flavour_spec_strips_editor_fields(monkeypatch):
    import mcp_server.server as srv
    monkeypatch.setattr(srv, "REPO_ROOT", REPO_ROOT)

    raw = srv.get_flavour_spec("acme-crm", "small", "appserver")
    result = json.loads(raw)

    editor_fields = {"ChangeState", "change", "prefix_content", "suffix_content", "image_type", "image_value"}
    def _check_no_editor_fields(obj):
        if isinstance(obj, dict):
            for key in editor_fields:
                assert key not in obj, f"Editor field '{key}' found in MCP response"
            for v in obj.values():
                _check_no_editor_fields(v)
        elif isinstance(obj, list):
            for item in obj:
                _check_no_editor_fields(item)

    _check_no_editor_fields(result)

import json
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures" / "minimal-infra"


def _tv(type_, unit, value=None, formula=None):
    d = {"type": type_, "unit": unit}
    if value is not None:
        d["value"] = value
    if formula is not None:
        d["formula"] = formula
    return d


def _minimal_server(**overrides):
    base = {
        "system": "Web",
        "cpu": _tv("static", "vCPU", value=4),
        "cpu_clocking": "3.0 GHz",
        "memory": _tv("static", "GB", value=16),
        "disk": [{"size": _tv("static", "GB", value=100), "performance": "SSD", "comment": "OS"}],
    }
    base.update(overrides)
    return base


# ── TypedValue: static ────────────────────────────────────────────────────────

def test_typed_value_static_render_integer():
    from src.loader import TypedValue
    tv = TypedValue(type="static", unit="vCPU", value=8.0)
    assert tv.render() == "8 vCPU"


def test_typed_value_static_render_no_decimal():
    from src.loader import TypedValue
    tv = TypedValue(type="static", unit="GB", value=32.0)
    assert tv.render() == "32 GB"


def test_typed_value_static_render_float():
    from src.loader import TypedValue
    tv = TypedValue(type="static", unit="TB", value=1.5)
    assert tv.render() == "1.5 TB"


def test_typed_value_dynamic_render():
    from src.loader import TypedValue
    tv = TypedValue(type="dynamic", unit="vCPU", formula="n × 4")
    assert tv.render() == "n × 4 vCPU"


# ── load_servers: valid ───────────────────────────────────────────────────────

def test_load_servers_valid(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    (flavour_dir / "servers.json").write_text(json.dumps([_minimal_server()]))

    servers = load_servers(flavour_dir)
    assert len(servers) == 1
    s = servers[0]
    assert s.system == "Web"
    assert s.count == 1
    assert s.network == []
    assert s.software == []
    assert s.comment == ""
    assert len(s.disk) == 1
    assert s.disk[0].comment == "OS"
    assert s.cpu.render() == "4 vCPU"
    assert s.memory.render() == "16 GB"
    assert s.disk[0].size.render() == "100 GB"


def test_load_servers_dynamic_cpu(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    entry = _minimal_server(cpu=_tv("dynamic", "vCPU", formula="n × 4"))
    (flavour_dir / "servers.json").write_text(json.dumps([entry]))

    servers = load_servers(flavour_dir)
    assert servers[0].cpu.render() == "n × 4 vCPU"


def test_load_servers_dynamic_partition_size(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    disk = [{"size": _tv("dynamic", "GB", formula="n × 500"), "performance": "SSD", "comment": "Data"}]
    entry = _minimal_server(disk=disk)
    (flavour_dir / "servers.json").write_text(json.dumps([entry]))

    servers = load_servers(flavour_dir)
    assert servers[0].disk[0].size.render() == "n × 500 GB"


def test_load_servers_count_defaults_to_1(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    (flavour_dir / "servers.json").write_text(json.dumps([_minimal_server()]))
    assert load_servers(flavour_dir)[0].count == 1


def test_load_servers_absent_network_software_default_empty(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    (flavour_dir / "servers.json").write_text(json.dumps([_minimal_server()]))
    s = load_servers(flavour_dir)[0]
    assert s.network == []
    assert s.software == []


# ── load_servers: validation errors ──────────────────────────────────────────

def test_load_servers_empty_disk_raises(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    (flavour_dir / "servers.json").write_text(json.dumps([_minimal_server(disk=[])]))
    with pytest.raises(ValueError, match="no disk partitions"):
        load_servers(flavour_dir)


def test_load_servers_invalid_typed_value_type_raises(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    entry = _minimal_server(cpu={"type": "unknown", "unit": "vCPU", "value": 4})
    (flavour_dir / "servers.json").write_text(json.dumps([entry]))
    with pytest.raises(ValueError, match="must be 'static' or 'dynamic'"):
        load_servers(flavour_dir)


def test_load_servers_missing_unit_raises(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    entry = _minimal_server(cpu={"type": "static", "value": 4})
    (flavour_dir / "servers.json").write_text(json.dumps([entry]))
    with pytest.raises(ValueError, match="unit is required"):
        load_servers(flavour_dir)


def test_load_servers_dynamic_missing_formula_raises(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    entry = _minimal_server(cpu={"type": "dynamic", "unit": "vCPU"})
    (flavour_dir / "servers.json").write_text(json.dumps([entry]))
    with pytest.raises(ValueError, match="formula is required"):
        load_servers(flavour_dir)


# ── load_product: orchestration ───────────────────────────────────────────────

def test_load_product_missing_sizes_json_returns_none(tmp_path):
    from src.loader import load_product

    (tmp_path / "infra" / "product-x").mkdir(parents=True)
    (tmp_path / "infra" / "product-x" / "prefix.adoc").write_text("")
    (tmp_path / "infra" / "product-x" / "suffix.adoc").write_text("")
    (tmp_path / "infra" / "product-x" / "meta.json").write_text(
        json.dumps({"prefix": "prefix.adoc", "suffix": "suffix.adoc"})
    )
    result = load_product(tmp_path, "product-x", "Product X")
    assert result is None


def test_load_product_error_isolation(tmp_path):
    from src.loader import load_product

    # Bad product: empty sizes.json
    (tmp_path / "infra" / "bad-product").mkdir(parents=True)
    (tmp_path / "infra" / "bad-product" / "prefix.adoc").write_text("")
    (tmp_path / "infra" / "bad-product" / "suffix.adoc").write_text("")
    (tmp_path / "infra" / "bad-product" / "meta.json").write_text(
        json.dumps({"prefix": "prefix.adoc", "suffix": "suffix.adoc"})
    )
    (tmp_path / "infra" / "bad-product" / "sizes.json").write_text("[]")

    # Good product: complete tree with TypedValue
    (tmp_path / "infra" / "good-product").mkdir(parents=True)
    (tmp_path / "infra" / "good-product" / "prefix.adoc").write_text("")
    (tmp_path / "infra" / "good-product" / "suffix.adoc").write_text("")
    (tmp_path / "infra" / "good-product" / "meta.json").write_text(
        json.dumps({"prefix": "prefix.adoc", "suffix": "suffix.adoc"})
    )
    (tmp_path / "infra" / "good-product" / "sizes.json").write_text(json.dumps(
        [{"shortname": "size-s", "display_name": "Small"}]
    ))
    size_dir = tmp_path / "infra" / "good-product" / "size-s"
    size_dir.mkdir()
    (size_dir / "meta.json").write_text(json.dumps({"prefix_text": "", "suffix_text": ""}))
    (size_dir / "flavours.json").write_text(json.dumps(
        [{"shortname": "flavour-f", "display_name": "F"}]
    ))
    fl_dir = size_dir / "flavour-f"
    fl_dir.mkdir()
    (fl_dir / "meta.json").write_text("{}")
    (fl_dir / "servers.json").write_text(json.dumps([_minimal_server()]))

    bad = load_product(tmp_path, "bad-product", "Bad Product")
    good = load_product(tmp_path, "good-product", "Good Product")

    assert bad is None
    assert good is not None
    assert good.shortname == "good-product"

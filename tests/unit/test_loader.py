import json
import sys
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures" / "minimal-infra"


def test_load_servers_valid(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    (flavour_dir / "servers.json").write_text(json.dumps([
        {
            "system": "Web",
            "cpu": "4 vCPU",
            "cpu_clocking": "3.0 GHz",
            "memory": "16 GB",
            "disk": [{"size": "100 GB", "performance": "SSD", "comment": "OS"}],
        }
    ]))
    servers = load_servers(flavour_dir)
    assert len(servers) == 1
    assert servers[0].system == "Web"
    assert servers[0].count == 1
    assert servers[0].network == []
    assert servers[0].software == []
    assert servers[0].comment == ""
    assert len(servers[0].disk) == 1
    assert servers[0].disk[0].comment == "OS"


def test_load_servers_empty_disk_raises(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    (flavour_dir / "servers.json").write_text(json.dumps([
        {
            "system": "Web",
            "cpu": "4 vCPU",
            "cpu_clocking": "3.0 GHz",
            "memory": "16 GB",
            "disk": [],
        }
    ]))
    with pytest.raises(ValueError, match="no disk partitions"):
        load_servers(flavour_dir)


def test_load_servers_count_defaults_to_1(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    (flavour_dir / "servers.json").write_text(json.dumps([
        {
            "system": "DB",
            "cpu": "8 vCPU",
            "cpu_clocking": "2.5 GHz",
            "memory": "64 GB",
            "disk": [{"size": "1 TB", "performance": "NVMe"}],
        }
    ]))
    servers = load_servers(flavour_dir)
    assert servers[0].count == 1


def test_load_servers_absent_network_software_default_empty(tmp_path):
    from src.loader import load_servers

    flavour_dir = tmp_path / "flavour"
    flavour_dir.mkdir()
    (flavour_dir / "servers.json").write_text(json.dumps([
        {
            "system": "DB",
            "cpu": "8 vCPU",
            "cpu_clocking": "2.5 GHz",
            "memory": "64 GB",
            "disk": [{"size": "1 TB", "performance": "NVMe"}],
        }
    ]))
    servers = load_servers(flavour_dir)
    assert servers[0].network == []
    assert servers[0].software == []


def test_load_product_missing_sizes_json_returns_none(tmp_path):
    from src.loader import load_product

    (tmp_path / "infra" / "product-x").mkdir(parents=True)
    (tmp_path / "infra" / "product-x" / "preamble.adoc").write_text("")
    (tmp_path / "infra" / "product-x" / "suffix.adoc").write_text("")
    (tmp_path / "infra" / "product-x" / "meta.json").write_text(
        json.dumps({"preamble": "preamble.adoc", "suffix": "suffix.adoc"})
    )
    # No sizes.json
    result = load_product(tmp_path, "product-x", "Product X")
    assert result is None


def test_load_product_error_isolation(tmp_path):
    from src.loader import load_product

    # Product with no sizes (sizes.json missing)
    (tmp_path / "infra" / "bad-product").mkdir(parents=True)
    (tmp_path / "infra" / "bad-product" / "preamble.adoc").write_text("")
    (tmp_path / "infra" / "bad-product" / "suffix.adoc").write_text("")
    (tmp_path / "infra" / "bad-product" / "meta.json").write_text(
        json.dumps({"preamble": "preamble.adoc", "suffix": "suffix.adoc"})
    )
    # sizes.json with empty array
    (tmp_path / "infra" / "bad-product" / "sizes.json").write_text("[]")

    # Valid product
    (tmp_path / "infra" / "good-product").mkdir(parents=True)
    (tmp_path / "infra" / "good-product" / "preamble.adoc").write_text("")
    (tmp_path / "infra" / "good-product" / "suffix.adoc").write_text("")
    (tmp_path / "infra" / "good-product" / "meta.json").write_text(
        json.dumps({"preamble": "preamble.adoc", "suffix": "suffix.adoc"})
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
    (fl_dir / "servers.json").write_text(json.dumps([
        {"system": "S", "cpu": "2 vCPU", "cpu_clocking": "2.0 GHz", "memory": "8 GB",
         "disk": [{"size": "100 GB", "performance": "SSD"}]}
    ]))

    errors = []
    bad = load_product(tmp_path, "bad-product", "Bad Product")
    good = load_product(tmp_path, "good-product", "Good Product")

    assert bad is None
    assert good is not None
    assert good.shortname == "good-product"

from __future__ import annotations
import json
from pathlib import Path

from services.loader import _load_flavour


def read_products(repo_root: Path) -> list[dict]:
    products_json = repo_root / "infra" / "products.json"
    if not products_json.exists():
        raise ValueError(f"infra/products.json not found at {products_json} — check REPO_ROOT")
    return json.loads(products_json.read_text())


def read_sizes(repo_root: Path, product: str) -> list[dict]:
    sizes_json = repo_root / "infra" / product / "sizes.json"
    if not sizes_json.exists():
        raise ValueError(f"Product '{product}' not found")
    return json.loads(sizes_json.read_text())


def read_flavours(repo_root: Path, product: str, size: str) -> list[dict]:
    flavours_json = repo_root / "infra" / product / size / "flavours.json"
    if not (repo_root / "infra" / product / "sizes.json").exists():
        raise ValueError(f"Product '{product}' not found")
    if not flavours_json.exists():
        raise ValueError(f"Size '{size}' not found for product '{product}'")
    return json.loads(flavours_json.read_text())


def _server_to_dict(server) -> dict:
    def tv(node) -> dict:
        d = {"type": node.type, "unit": node.unit}
        if node.value is not None:
            d["value"] = node.value
        if node.formula is not None:
            d["formula"] = node.formula
        return d

    return {
        "system": server.system,
        "count": server.count,
        "cpu": tv(server.cpu),
        "cpu_clocking": server.cpu_clocking,
        "memory": tv(server.memory),
        "disk": [
            {
                "size": tv(p.size),
                "performance": p.performance,
                "comment": p.comment,
            }
            for p in server.disk
        ],
        "network": server.network,
        "software": server.software,
        "comment": server.comment,
    }


def read_flavour_spec(repo_root: Path, product: str, size: str, flavour: str) -> dict:
    sizes_json = repo_root / "infra" / product / "sizes.json"
    if not sizes_json.exists():
        raise ValueError(f"Product '{product}' not found")

    flavours_json = repo_root / "infra" / product / size / "flavours.json"
    if not flavours_json.exists():
        raise ValueError(f"Size '{size}' not found for product '{product}'")

    entries = json.loads(flavours_json.read_text())
    entry = next((e for e in entries if e["shortname"] == flavour), None)
    if entry is None:
        raise ValueError(f"Flavour '{flavour}' not found for product '{product}' size '{size}'")

    size_dir = repo_root / "infra" / product / size
    node = _load_flavour(flavour, entry["display_name"], size_dir)

    return {
        "shortname": node.shortname,
        "display_name": node.display_name,
        "servers": [_server_to_dict(s) for s in node.servers],
    }

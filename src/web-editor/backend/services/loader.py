from __future__ import annotations
import json
from pathlib import Path

from models.state import (
    ChangeState, EditorState, FlavourNode, PartitionNode,
    ProductNode, ServerNode, SizeNode, TypedValueNode, UnitsNode,
)

DEFAULT_UNITS = ["vCPU", "GB", "GiB", "TB", "TiB", "GHz", "MHz"]


def _tv_node(raw: dict) -> TypedValueNode:
    return TypedValueNode(
        type=raw["type"],
        unit=raw["unit"],
        value=raw.get("value"),
        formula=raw.get("formula"),
    )


def _load_servers(flavour_dir: Path) -> list[ServerNode]:
    data = json.loads((flavour_dir / "servers.json").read_text())
    nodes = []
    for s in data:
        disk = [
            PartitionNode(
                size=_tv_node(p["size"]),
                performance=p.get("performance", ""),
                comment=p.get("comment", ""),
            )
            for p in s.get("disk", [])
        ]
        nodes.append(ServerNode(
            system=s.get("system", ""),
            count=s.get("count", 1),
            cpu=_tv_node(s["cpu"]),
            cpu_clocking=s.get("cpu_clocking", ""),
            memory=_tv_node(s["memory"]),
            disk=disk,
            network=s.get("network", []),
            software=s.get("software", []),
            comment=s.get("comment", ""),
        ))
    return nodes


def _load_flavour(shortname: str, display_name: str, size_dir: Path) -> FlavourNode:
    flavour_dir = size_dir / shortname
    meta_path = flavour_dir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    image = meta.get("image")
    preamble_path = flavour_dir / "preamble.adoc"
    suffix_path = flavour_dir / "suffix.adoc"

    servers = _load_servers(flavour_dir)

    return FlavourNode(
        shortname=shortname,
        display_name=display_name,
        image_type=image["type"] if image else None,
        image_value=image["value"] if image else None,
        preamble_content=preamble_path.read_text() if preamble_path.exists() else "",
        suffix_content=suffix_path.read_text() if suffix_path.exists() else "",
        servers=servers,
    )


def _load_size(entry: dict, product_dir: Path) -> SizeNode:
    shortname = entry["shortname"]
    size_dir = product_dir / shortname
    meta = json.loads((size_dir / "meta.json").read_text()) if (size_dir / "meta.json").exists() else {}

    flavour_entries = json.loads((size_dir / "flavours.json").read_text())
    flavours: dict[str, FlavourNode] = {}
    for fe in flavour_entries:
        flavours[fe["shortname"]] = _load_flavour(fe["shortname"], fe["display_name"], size_dir)

    return SizeNode(
        shortname=shortname,
        display_name=entry["display_name"],
        prefix_text=meta.get("prefix_text", ""),
        suffix_text=meta.get("suffix_text", ""),
        flavours=flavours,
    )


def _load_product(shortname: str, display_name: str, repo_root: Path) -> ProductNode:
    product_dir = repo_root / "infra" / shortname
    try:
        meta = json.loads((product_dir / "meta.json").read_text())
        preamble_path = product_dir / meta.get("preamble", "preamble.adoc")
        suffix_path = product_dir / meta.get("suffix", "suffix.adoc")

        size_entries = json.loads((product_dir / "sizes.json").read_text())
        sizes: dict[str, SizeNode] = {}
        for se in size_entries:
            sizes[se["shortname"]] = _load_size(se, product_dir)

        return ProductNode(
            shortname=shortname,
            display_name=display_name,
            preamble_content=preamble_path.read_text() if preamble_path.exists() else "",
            suffix_content=suffix_path.read_text() if suffix_path.exists() else "",
            sizes=sizes,
        )
    except Exception as exc:
        return ProductNode(
            shortname=shortname,
            display_name=display_name,
            change=ChangeState.ERROR,
            error=str(exc),
        )


def load_infra(repo_root: Path) -> EditorState:
    infra_dir = repo_root / "infra"
    products: dict[str, ProductNode] = {}

    products_json = infra_dir / "products.json"
    if products_json.exists():
        entries = json.loads(products_json.read_text())
        for entry in entries:
            sn = entry["shortname"]
            products[sn] = _load_product(sn, entry["display_name"], repo_root)

    units_json = infra_dir / "units.json"
    if units_json.exists():
        units = UnitsNode(units=json.loads(units_json.read_text()))
    else:
        units = UnitsNode(units=list(DEFAULT_UNITS), change=ChangeState.ADDED)

    return EditorState(products=products, units=units)

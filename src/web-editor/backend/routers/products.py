from __future__ import annotations
import copy
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import state_store
from services.loader import _load_product
from models.state import (
    ChangeState, FlavourNode, PartitionNode, ProductNode,
    ServerNode, SizeNode, TypedValueNode,
)
import os
from pathlib import Path

router = APIRouter()
REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parents[5]))


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_product(shortname: str) -> ProductNode:
    state = state_store.get_state()
    p = state.products.get(shortname)
    if not p:
        raise HTTPException(404, f"Product '{shortname}' not found")
    return p


def _get_size(product: str, size: str) -> SizeNode:
    p = _get_product(product)
    s = p.sizes.get(size)
    if not s:
        raise HTTPException(404, f"Size '{size}' not found")
    return s


def _get_flavour(product: str, size: str, flavour: str) -> FlavourNode:
    s = _get_size(product, size)
    f = s.flavours.get(flavour)
    if not f:
        raise HTTPException(404, f"Flavour '{flavour}' not found")
    return f


def _tv_dict(tv: TypedValueNode) -> dict:
    d = {"type": tv.type, "unit": tv.unit, "invalid": tv.invalid}
    if tv.type == "static":
        d["value"] = tv.value
    else:
        d["formula"] = tv.formula
    return d


def _server_dict(s: ServerNode) -> dict:
    return {
        "system": s.system, "count": s.count,
        "cpu": _tv_dict(s.cpu), "cpu_clocking": s.cpu_clocking,
        "memory": _tv_dict(s.memory),
        "disk": [{"size": _tv_dict(p.size), "performance": p.performance, "comment": p.comment} for p in s.disk],
        "network": s.network, "software": s.software, "comment": s.comment,
        "change": s.change,
    }


def _unique_shortname(existing: dict, base: str) -> str:
    if base not in existing:
        return base
    candidate = f"{base}-copy"
    counter = 2
    while candidate in existing:
        candidate = f"{base}-copy-{counter}"
        counter += 1
    return candidate


def _mark_modified(p: ProductNode) -> None:
    if p.change == ChangeState.CLEAN:
        p.change = ChangeState.MODIFIED


# ── Products ──────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    shortname: str
    display_name: str


class ProductUpdate(BaseModel):
    display_name: str


@router.get("/products/{shortname}")
def get_product(shortname: str):
    p = _get_product(shortname)
    return {
        "shortname": p.shortname, "display_name": p.display_name,
        "change": p.change, "error": p.error,
        "preamble_change": p.preamble_change, "suffix_change": p.suffix_change,
        "sizes": {sn: {
            "shortname": s.shortname, "display_name": s.display_name,
            "prefix_text": s.prefix_text, "suffix_text": s.suffix_text, "change": s.change,
        } for sn, s in p.sizes.items()},
    }


@router.post("/products", status_code=201)
def create_product(body: ProductCreate):
    state = state_store.get_state()
    if body.shortname in state.products:
        raise HTTPException(409, f"shortname '{body.shortname}' already exists")
    node = ProductNode(shortname=body.shortname, display_name=body.display_name, change=ChangeState.ADDED)
    state.products[body.shortname] = node
    return {"shortname": node.shortname, "display_name": node.display_name, "change": node.change}


@router.put("/products/{shortname}")
def update_product(shortname: str, body: ProductUpdate):
    p = _get_product(shortname)
    p.display_name = body.display_name
    _mark_modified(p)
    return {"shortname": p.shortname, "display_name": p.display_name, "change": p.change}


@router.delete("/products/{shortname}")
def delete_product(shortname: str):
    p = _get_product(shortname)
    if p.change == ChangeState.ADDED:
        state_store.get_state().products.pop(shortname)
    else:
        p.change = ChangeState.DELETED
    return {"change": ChangeState.DELETED}


@router.post("/products/{shortname}/reset")
def reset_product(shortname: str):
    state = state_store.get_state()
    node = _load_product(shortname, state.products.get(shortname, ProductNode(shortname=shortname, display_name="")).display_name, REPO_ROOT)
    state.products[shortname] = node
    return {"shortname": node.shortname, "change": node.change}


# ── Sizes ─────────────────────────────────────────────────────────────────────

class SizeCreate(BaseModel):
    shortname: str
    display_name: str
    prefix_text: str = ""
    suffix_text: str = ""


class SizeUpdate(BaseModel):
    display_name: str
    prefix_text: str = ""
    suffix_text: str = ""


@router.get("/products/{product}/sizes/{size}")
def get_size(product: str, size: str):
    s = _get_size(product, size)
    return {"shortname": s.shortname, "display_name": s.display_name,
            "prefix_text": s.prefix_text, "suffix_text": s.suffix_text, "change": s.change}


@router.post("/products/{product}/sizes", status_code=201)
def create_size(product: str, body: SizeCreate):
    p = _get_product(product)
    if body.shortname in p.sizes:
        raise HTTPException(409, f"shortname '{body.shortname}' already exists")
    node = SizeNode(shortname=body.shortname, display_name=body.display_name,
                    prefix_text=body.prefix_text, suffix_text=body.suffix_text, change=ChangeState.ADDED)
    p.sizes[body.shortname] = node
    _mark_modified(p)
    return {"shortname": node.shortname, "display_name": node.display_name, "change": node.change}


@router.put("/products/{product}/sizes/{size}")
def update_size(product: str, size: str, body: SizeUpdate):
    p = _get_product(product)
    s = _get_size(product, size)
    s.display_name = body.display_name
    s.prefix_text = body.prefix_text
    s.suffix_text = body.suffix_text
    if s.change == ChangeState.CLEAN:
        s.change = ChangeState.MODIFIED
    _mark_modified(p)
    return {"shortname": s.shortname, "display_name": s.display_name, "change": s.change}


@router.delete("/products/{product}/sizes/{size}")
def delete_size(product: str, size: str):
    p = _get_product(product)
    s = _get_size(product, size)
    if s.change == ChangeState.ADDED:
        p.sizes.pop(size)
    else:
        s.change = ChangeState.DELETED
    return {"change": ChangeState.DELETED}


# ── Flavours ──────────────────────────────────────────────────────────────────

class FlavourCreate(BaseModel):
    shortname: str
    display_name: str


class FlavourUpdate(BaseModel):
    display_name: str
    image_type: str | None = None
    image_value: str | None = None


class CopyFlavour(BaseModel):
    target_product: str
    target_size: str


@router.get("/products/{product}/sizes/{size}/flavours/{flavour}")
def get_flavour(product: str, size: str, flavour: str):
    f = _get_flavour(product, size, flavour)
    return {"shortname": f.shortname, "display_name": f.display_name,
            "image_type": f.image_type, "image_value": f.image_value, "change": f.change}


@router.post("/products/{product}/sizes/{size}/flavours", status_code=201)
def create_flavour(product: str, size: str, body: FlavourCreate):
    p = _get_product(product)
    s = _get_size(product, size)
    if body.shortname in s.flavours:
        raise HTTPException(409, f"shortname '{body.shortname}' already exists")
    node = FlavourNode(shortname=body.shortname, display_name=body.display_name, change=ChangeState.ADDED)
    s.flavours[body.shortname] = node
    _mark_modified(p)
    return {"shortname": node.shortname, "display_name": node.display_name, "change": node.change}


@router.put("/products/{product}/sizes/{size}/flavours/{flavour}")
def update_flavour(product: str, size: str, flavour: str, body: FlavourUpdate):
    p = _get_product(product)
    f = _get_flavour(product, size, flavour)
    f.display_name = body.display_name
    f.image_type = body.image_type
    f.image_value = body.image_value
    if f.change == ChangeState.CLEAN:
        f.change = ChangeState.MODIFIED
    _mark_modified(p)
    return {"shortname": f.shortname, "display_name": f.display_name, "change": f.change}


@router.delete("/products/{product}/sizes/{size}/flavours/{flavour}")
def delete_flavour(product: str, size: str, flavour: str):
    p = _get_product(product)
    s = _get_size(product, size)
    f = _get_flavour(product, size, flavour)
    if f.change == ChangeState.ADDED:
        s.flavours.pop(flavour)
    else:
        f.change = ChangeState.DELETED
    return {"change": ChangeState.DELETED}


@router.post("/products/{product}/sizes/{size}/flavours/{flavour}/copy", status_code=201)
def copy_flavour(product: str, size: str, flavour: str, body: CopyFlavour):
    state = state_store.get_state()
    f = _get_flavour(product, size, flavour)
    target_p = state.products.get(body.target_product)
    if not target_p:
        raise HTTPException(422, f"Target product '{body.target_product}' not found")
    target_s = target_p.sizes.get(body.target_size)
    if not target_s:
        raise HTTPException(422, f"Target size '{body.target_size}' not found")

    new_sn = _unique_shortname(target_s.flavours, f.shortname)
    new_f = copy.deepcopy(f)
    new_f.shortname = new_sn
    new_f.change = ChangeState.ADDED
    target_s.flavours[new_sn] = new_f
    _mark_modified(target_p)
    return {"shortname": new_sn, "change": ChangeState.ADDED}


# ── Servers ───────────────────────────────────────────────────────────────────

class TypedValueIn(BaseModel):
    type: str
    unit: str
    value: float | None = None
    formula: str | None = None


class PartitionIn(BaseModel):
    size: TypedValueIn
    performance: str
    comment: str = ""


class ServerIn(BaseModel):
    system: str
    count: int = 1
    cpu: TypedValueIn
    cpu_clocking: str
    memory: TypedValueIn
    disk: list[PartitionIn]
    network: list[str] = []
    software: list[str] = []
    comment: str = ""


def _tv_node_from(tv: TypedValueIn) -> TypedValueNode:
    return TypedValueNode(type=tv.type, unit=tv.unit, value=tv.value, formula=tv.formula)


@router.get("/products/{product}/sizes/{size}/flavours/{flavour}/servers")
def get_servers(product: str, size: str, flavour: str):
    f = _get_flavour(product, size, flavour)
    return {"servers": [_server_dict(s) for s in f.servers]}


@router.post("/products/{product}/sizes/{size}/flavours/{flavour}/servers", status_code=201)
def add_server(product: str, size: str, flavour: str, body: ServerIn):
    p = _get_product(product)
    f = _get_flavour(product, size, flavour)
    node = ServerNode(
        system=body.system, count=body.count,
        cpu=_tv_node_from(body.cpu), cpu_clocking=body.cpu_clocking,
        memory=_tv_node_from(body.memory),
        disk=[PartitionNode(size=_tv_node_from(pt.size), performance=pt.performance, comment=pt.comment) for pt in body.disk],
        network=body.network, software=body.software, comment=body.comment,
        change=ChangeState.ADDED,
    )
    f.servers.append(node)
    _mark_modified(p)
    return {"index": len(f.servers) - 1, "server": _server_dict(node)}


@router.put("/products/{product}/sizes/{size}/flavours/{flavour}/servers/{index}")
def update_server(product: str, size: str, flavour: str, index: int, body: ServerIn):
    p = _get_product(product)
    f = _get_flavour(product, size, flavour)
    if index < 0 or index >= len(f.servers):
        raise HTTPException(404, f"Server index {index} out of range")
    node = ServerNode(
        system=body.system, count=body.count,
        cpu=_tv_node_from(body.cpu), cpu_clocking=body.cpu_clocking,
        memory=_tv_node_from(body.memory),
        disk=[PartitionNode(size=_tv_node_from(pt.size), performance=pt.performance, comment=pt.comment) for pt in body.disk],
        network=body.network, software=body.software, comment=body.comment,
        change=ChangeState.MODIFIED,
    )
    f.servers[index] = node
    _mark_modified(p)
    return _server_dict(node)


@router.delete("/products/{product}/sizes/{size}/flavours/{flavour}/servers/{index}")
def delete_server(product: str, size: str, flavour: str, index: int):
    p = _get_product(product)
    f = _get_flavour(product, size, flavour)
    if index < 0 or index >= len(f.servers):
        raise HTTPException(404, f"Server index {index} out of range")
    srv = f.servers[index]
    if srv.change == ChangeState.ADDED:
        f.servers.pop(index)
    else:
        srv.change = ChangeState.DELETED
    _mark_modified(p)
    return {"change": ChangeState.DELETED}

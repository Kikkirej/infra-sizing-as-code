from __future__ import annotations
from fastapi import APIRouter
from services import state_store
from models.state import ChangeState

router = APIRouter()


def _tv_dict(tv) -> dict:
    d = {"type": tv.type, "unit": tv.unit, "invalid": tv.invalid}
    if tv.type == "static":
        d["value"] = tv.value
    else:
        d["formula"] = tv.formula
    return d


def _server_dict(s) -> dict:
    return {
        "system": s.system, "count": s.count,
        "cpu": _tv_dict(s.cpu), "cpu_clocking": s.cpu_clocking,
        "memory": _tv_dict(s.memory),
        "disk": [{"size": _tv_dict(p.size), "performance": p.performance, "comment": p.comment} for p in s.disk],
        "network": s.network, "software": s.software, "comment": s.comment,
        "change": s.change,
    }


def _flavour_tree(f) -> dict:
    return {
        "shortname": f.shortname, "display_name": f.display_name,
        "image_type": f.image_type, "image_value": f.image_value,
        "change": f.change,
        "has_preamble": bool(f.preamble_content),
        "has_suffix": bool(f.suffix_content),
        "preamble_change": f.preamble_change, "suffix_change": f.suffix_change,
        "servers": [_server_dict(s) for s in f.servers],
    }


@router.get("/tree")
def get_tree():
    state = state_store.get_state()
    products_out = {}
    for sn, p in state.products.items():
        sizes_out = {}
        for ssn, s in p.sizes.items():
            flavours_out = {fn: _flavour_tree(f) for fn, f in s.flavours.items()}
            sizes_out[ssn] = {
                "shortname": s.shortname, "display_name": s.display_name,
                "prefix_text": s.prefix_text, "suffix_text": s.suffix_text,
                "change": s.change, "flavours": flavours_out,
            }
        products_out[sn] = {
            "shortname": p.shortname, "display_name": p.display_name,
            "change": p.change, "error": p.error,
            "has_preamble": bool(p.preamble_content),
            "has_suffix": bool(p.suffix_content),
            "preamble_change": p.preamble_change, "suffix_change": p.suffix_change,
            "sizes": sizes_out,
        }
    return {"products": products_out}


@router.get("/overview")
def get_overview():
    state = state_store.get_state()
    items = []
    for sn, p in state.products.items():
        if p.change == ChangeState.DELETED:
            continue
        size_count = sum(1 for s in p.sizes.values() if s.change != ChangeState.DELETED)
        flavour_count = sum(
            1 for s in p.sizes.values() if s.change != ChangeState.DELETED
            for f in s.flavours.values() if f.change != ChangeState.DELETED
        )
        server_count = sum(
            1 for s in p.sizes.values() if s.change != ChangeState.DELETED
            for f in s.flavours.values() if f.change != ChangeState.DELETED
            for sv in f.servers if sv.change != ChangeState.DELETED
        )
        items.append({
            "shortname": p.shortname, "display_name": p.display_name,
            "size_count": size_count, "flavour_count": flavour_count,
            "server_count": server_count, "has_error": p.change == ChangeState.ERROR,
        })
    return {"products": items}

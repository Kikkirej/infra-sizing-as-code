from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import state_store
from models.state import ChangeState

router = APIRouter()


class AdocUpdate(BaseModel):
    content: str


@router.get("/adoc/{path:path}")
def get_adoc(path: str):
    state = state_store.get_state()
    parts = path.split("/")

    if len(parts) == 3 and parts[0] == "infra":
        product_sn = parts[1]
        filename = parts[2].replace(".adoc", "")
        p = state.products.get(product_sn)
        if not p:
            raise HTTPException(404, "Product not found")
        content = p.preamble_content if filename == "preamble" else p.suffix_content
        change = p.preamble_change if filename == "preamble" else p.suffix_change
        return {"path": path, "content": content, "change": change}

    if len(parts) == 6 and parts[0] == "infra":
        product_sn, size_sn, flavour_sn = parts[1], parts[2], parts[3]
        filename = parts[5].replace(".adoc", "")
        p = state.products.get(product_sn)
        if not p:
            raise HTTPException(404, "Product not found")
        s = p.sizes.get(size_sn)
        if not s:
            raise HTTPException(404, "Size not found")
        f = s.flavours.get(flavour_sn)
        if not f:
            raise HTTPException(404, "Flavour not found")
        content = f.preamble_content if filename == "preamble" else f.suffix_content
        change = f.preamble_change if filename == "preamble" else f.suffix_change
        return {"path": path, "content": content, "change": change}

    raise HTTPException(400, "Unrecognised adoc path")


@router.put("/adoc/{path:path}")
def update_adoc(path: str, body: AdocUpdate):
    state = state_store.get_state()
    parts = path.split("/")

    if len(parts) == 3 and parts[0] == "infra":
        product_sn = parts[1]
        filename = parts[2].replace(".adoc", "")
        p = state.products.get(product_sn)
        if not p:
            raise HTTPException(404, "Product not found")
        if filename == "preamble":
            p.preamble_content = body.content
            p.preamble_change = ChangeState.MODIFIED
        else:
            p.suffix_content = body.content
            p.suffix_change = ChangeState.MODIFIED
        if p.change == ChangeState.CLEAN:
            p.change = ChangeState.MODIFIED
        return {"path": path, "change": ChangeState.MODIFIED}

    if len(parts) == 6 and parts[0] == "infra":
        product_sn, size_sn, flavour_sn = parts[1], parts[2], parts[3]
        filename = parts[5].replace(".adoc", "")
        p = state.products.get(product_sn)
        s = p.sizes.get(size_sn) if p else None
        f = s.flavours.get(flavour_sn) if s else None
        if not f:
            raise HTTPException(404, "Entity not found")
        if filename == "preamble":
            f.preamble_content = body.content
            f.preamble_change = ChangeState.MODIFIED
        else:
            f.suffix_content = body.content
            f.suffix_change = ChangeState.MODIFIED
        if f.change == ChangeState.CLEAN:
            f.change = ChangeState.MODIFIED
        if p.change == ChangeState.CLEAN:
            p.change = ChangeState.MODIFIED
        return {"path": path, "change": ChangeState.MODIFIED}

    raise HTTPException(400, "Unrecognised adoc path")

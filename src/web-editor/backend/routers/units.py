from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services import state_store
from models.state import ChangeState

router = APIRouter()


class UnitCreate(BaseModel):
    unit: str


@router.get("/units")
def get_units():
    state = state_store.get_state()
    return {"units": state.units.units, "change": state.units.change}


@router.post("/units", status_code=201)
def add_unit(body: UnitCreate):
    state = state_store.get_state()
    if body.unit in state.units.units:
        raise HTTPException(409, f"Unit '{body.unit}' already exists")
    state.units.units.append(body.unit)
    if state.units.change == ChangeState.CLEAN:
        state.units.change = ChangeState.MODIFIED
    return {"units": state.units.units, "change": state.units.change}


@router.delete("/units/{unit}")
def delete_unit(unit: str):
    state = state_store.get_state()
    if unit not in state.units.units:
        raise HTTPException(404, f"Unit '{unit}' not found")

    affected_paths: list[str] = []
    for p in state.products.values():
        for s in p.sizes.values():
            for f in s.flavours.values():
                for i, srv in enumerate(f.servers):
                    for tv_name in ("cpu", "memory"):
                        tv = getattr(srv, tv_name)
                        if tv.unit == unit:
                            tv.invalid = True
                            affected_paths.append(f"{p.shortname} / {s.shortname} / {f.shortname} / server[{i}].{tv_name}")
                    for j, part in enumerate(srv.disk):
                        if part.size.unit == unit:
                            part.size.invalid = True
                            affected_paths.append(f"{p.shortname} / {s.shortname} / {f.shortname} / server[{i}].disk[{j}].size")

    state.units.units.remove(unit)
    if state.units.change == ChangeState.CLEAN:
        state.units.change = ChangeState.MODIFIED

    return {"unit": unit, "affected_count": len(affected_paths), "affected_paths": affected_paths}

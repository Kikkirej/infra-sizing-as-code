from __future__ import annotations
import json
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from models.versioning import VersionEntry, VersionFile, _validate_version_name

router = APIRouter()
REPO_ROOT = Path(os.environ.get("REPO_ROOT", "."))


# ── helpers ──────────────────────────────────────────────────────────────────

def _versioning_dir(shortname: str) -> Path:
    return REPO_ROOT / "infra" / shortname / "versioning"


def _wip_path(shortname: str) -> Path:
    return _versioning_dir(shortname) / "wip.json"


def _released_path(shortname: str, version_name: str) -> Path:
    return _versioning_dir(shortname) / f"{version_name}.json"


def _product_exists(shortname: str) -> bool:
    return (REPO_ROOT / "infra" / shortname).is_dir()


def _read_version_file(path: Path) -> dict:
    return json.loads(path.read_text())


def _write_version_file(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _load_wip(shortname: str) -> tuple[dict, bool]:
    """Return (raw_dict, is_malformed). Raises 404 if wip.json missing."""
    path = _wip_path(shortname)
    if not path.exists():
        return None, False
    try:
        raw = _read_version_file(path)
        if not isinstance(raw, dict) or "version_name" not in raw or "entries" not in raw:
            return None, True
        return raw, False
    except Exception:
        return None, True


# ── US1: list & get ──────────────────────────────────────────────────────────

@router.get("/products/{shortname}/versioning")
def list_versions(shortname: str):
    if not _product_exists(shortname):
        raise HTTPException(404, f"Product '{shortname}' not found")
    vdir = _versioning_dir(shortname)
    if not vdir.is_dir():
        return {"wip": False, "versions": []}
    has_wip = (_wip_path(shortname)).exists()
    released = sorted(
        [p.stem for p in vdir.glob("*.json") if p.stem != "wip"],
        key=lambda s: -(_released_path(shortname, s).stat().st_mtime),
    )
    return {"wip": has_wip, "versions": released}


@router.get("/products/{shortname}/versioning/{version}")
def get_version(shortname: str, version: str):
    if not _product_exists(shortname):
        raise HTTPException(404, f"Product '{shortname}' not found")
    if version == "wip":
        path = _wip_path(shortname)
        if not path.exists():
            return {"version_name": "", "entries": [], "readonly": False}
        raw, malformed = _load_wip(shortname)
        if malformed:
            raise HTTPException(
                422,
                "wip.json is malformed or has an unexpected structure. "
                "Use POST /api/products/{shortname}/versioning/wip/reset to create a fresh WIP.",
            )
        return {**raw, "readonly": False}
    path = _released_path(shortname, version)
    if not path.exists():
        raise HTTPException(404, f"Version '{version}' not found for product '{shortname}'")
    try:
        raw = _read_version_file(path)
    except Exception:
        raise HTTPException(422, f"Version file '{version}.json' is malformed")
    return {**raw, "readonly": True}


# ── US1: reset malformed WIP ─────────────────────────────────────────────────

@router.post("/products/{shortname}/versioning/wip/reset")
def reset_wip(shortname: str):
    if not _product_exists(shortname):
        raise HTTPException(404, f"Product '{shortname}' not found")
    fresh = {"version_name": "", "entries": []}
    _write_version_file(_wip_path(shortname), fresh)
    return {**fresh, "readonly": False}


# ── US2: update version_name ─────────────────────────────────────────────────

class VersionNameUpdate(BaseModel):
    version_name: str

    @field_validator("version_name")
    @classmethod
    def validate_vn(cls, v: str) -> str:
        if v:
            return _validate_version_name(v)
        return v


@router.patch("/products/{shortname}/versioning/wip")
def update_version_name(shortname: str, body: VersionNameUpdate):
    if not _product_exists(shortname):
        raise HTTPException(404, f"Product '{shortname}' not found")
    raw, malformed = _load_wip(shortname)
    if malformed:
        raise HTTPException(422, "wip.json is malformed. Use /wip/reset first.")
    if raw is None:
        raw = {"version_name": "", "entries": []}
    raw["version_name"] = body.version_name
    _write_version_file(_wip_path(shortname), raw)
    return {"version_name": body.version_name}


# ── US2: entry CRUD ───────────────────────────────────────────────────────────

@router.post("/products/{shortname}/versioning/wip/entries", status_code=201)
def create_entry(shortname: str, body: VersionEntry):
    if not _product_exists(shortname):
        raise HTTPException(404, f"Product '{shortname}' not found")
    raw, malformed = _load_wip(shortname)
    if malformed:
        raise HTTPException(422, "wip.json is malformed. Use /wip/reset first.")
    if raw is None:
        raw = {"version_name": "", "entries": []}
    entry = body.model_dump()
    raw["entries"].append(entry)
    _write_version_file(_wip_path(shortname), raw)
    return {"index": len(raw["entries"]) - 1, "entry": entry}


@router.put("/products/{shortname}/versioning/wip/entries/{index}")
def update_entry(shortname: str, index: int, body: VersionEntry):
    if not _product_exists(shortname):
        raise HTTPException(404, f"Product '{shortname}' not found")
    raw, malformed = _load_wip(shortname)
    if malformed:
        raise HTTPException(422, "wip.json is malformed. Use /wip/reset first.")
    if raw is None or index < 0 or index >= len(raw.get("entries", [])):
        raise HTTPException(404, f"Entry index {index} out of range")
    entry = body.model_dump()
    raw["entries"][index] = entry
    _write_version_file(_wip_path(shortname), raw)
    return entry


@router.delete("/products/{shortname}/versioning/wip/entries/{index}")
def delete_entry(shortname: str, index: int):
    if not _product_exists(shortname):
        raise HTTPException(404, f"Product '{shortname}' not found")
    raw, malformed = _load_wip(shortname)
    if malformed:
        raise HTTPException(422, "wip.json is malformed. Use /wip/reset first.")
    if raw is None or index < 0 or index >= len(raw.get("entries", [])):
        raise HTTPException(404, f"Entry index {index} out of range")
    raw["entries"].pop(index)
    _write_version_file(_wip_path(shortname), raw)
    return {"deleted": True}


# ── US3: release ─────────────────────────────────────────────────────────────

class ReleaseBody(BaseModel):
    new_version_name: str

    @field_validator("new_version_name")
    @classmethod
    def validate_nvn(cls, v: str) -> str:
        return _validate_version_name(v)


@router.post("/products/{shortname}/release")
def release_product(shortname: str, body: ReleaseBody):
    import sys
    from pathlib import Path as _Path

    if not _product_exists(shortname):
        raise HTTPException(404, f"Product '{shortname}' not found")

    # Step 1-3: read & validate wip.json
    raw, malformed = _load_wip(shortname)
    if malformed:
        raise HTTPException(422, "wip.json is malformed. Use /wip/reset first.")
    if raw is None:
        raise HTTPException(422, "wip.json not found. Nothing to release.")

    entries = raw.get("entries", [])
    if not entries:
        raise HTTPException(422, "Cannot release a version with no change entries.")

    version_name = raw.get("version_name", "")
    if not version_name:
        raise HTTPException(422, "WIP version_name is empty. Set a version name before releasing.")
    try:
        _validate_version_name(version_name)
    except ValueError as e:
        raise HTTPException(422, str(e))

    # Step 3: check no duplicate
    released_path = _released_path(shortname, version_name)
    if released_path.exists():
        raise HTTPException(
            409,
            f"Version {version_name} already exists. Please change the WIP version name.",
        )

    # Step 5: write released version file
    _write_version_file(released_path, raw)

    # Step 6-7: regenerate .adoc and attempt PDF
    pdf_generated = False
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from src.versioning import VersionFileData, VersionEntryData
        from src.loader import load_product
        from src.renderer import render_product_document

        # Build VersionFileData for the renderer
        vf = VersionFileData(
            version_name=version_name,
            entries=[
                VersionEntryData(author=e["author"], date=e["date"], notes=e.get("notes"))
                for e in entries
            ],
        )

        product = load_product(REPO_ROOT, shortname, shortname)
        if product is not None:
            product.version_file = vf
            adoc_content = render_product_document(product)
            output_dir = REPO_ROOT / "output"
            output_dir.mkdir(exist_ok=True)
            adoc_path = output_dir / f"{shortname}.adoc"
            adoc_path.write_text(adoc_content)

            # Attempt PDF build
            try:
                import subprocess
                result = subprocess.run(
                    ["asciidoctor-pdf", "-o", str(output_dir / f"{shortname}.pdf"), str(adoc_path)],
                    capture_output=True, timeout=120,
                )
                pdf_generated = result.returncode == 0
            except Exception:
                pass
    except Exception as exc:
        print(f"[release] .adoc/PDF generation failed: {exc}", file=sys.stderr)

    # Step 8: seed new wip.json
    last_entry = entries[-1]
    new_wip = {
        "version_name": body.new_version_name,
        "entries": [{
            "author": last_entry["author"],
            "date": last_entry["date"],
            "notes": "copied from previous version",
        }],
    }
    _write_version_file(_wip_path(shortname), new_wip)

    # Steps 9-10: commit + tag
    commit_sha = None
    tag = f"{shortname}-{version_name}"
    try:
        from git import Repo
        repo = Repo(REPO_ROOT)
        repo.git.add(A=True)
        commit_obj = repo.index.commit(f"release({shortname}): {version_name}")
        commit_sha = commit_obj.hexsha[:7]
        repo.create_tag(tag)
    except Exception as exc:
        raise HTTPException(500, f"Git operation failed: {exc}")

    return {
        "version_name": version_name,
        "tag": tag,
        "commit_sha": commit_sha,
        "pdf_generated": pdf_generated,
        "new_wip_version_name": body.new_version_name,
    }

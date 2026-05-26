from __future__ import annotations
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse
from services import state_store
from services.writer import atomic_write_text

router = APIRouter()
REPO_ROOT = Path(os.environ.get("REPO_ROOT", "."))

ALLOWED_TYPES = {"image/png", "image/svg+xml"}
ALLOWED_EXTENSIONS = {".png", ".svg", ".mmd"}


@router.post("/files/upload/{product}/{size}/{flavour}")
async def upload_file(product: str, size: str, flavour: str, file: UploadFile):
    ext = Path(file.filename).suffix.lower()
    if file.content_type not in ALLOWED_TYPES and ext != ".mmd":
        raise HTTPException(422, f"Unsupported file type: {file.content_type} / {ext}")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(422, f"Unsupported extension: {ext}")

    state = state_store.get_state()
    p = state.products.get(product)
    s = p.sizes.get(size) if p else None
    f = s.flavours.get(flavour) if s else None
    if not f:
        raise HTTPException(404, "Flavour not found")

    flavour_dir = REPO_ROOT / "infra" / product / size / flavour
    target = flavour_dir / file.filename

    content = await file.read()
    flavour_dir.mkdir(parents=True, exist_ok=True)

    fd, tmp = tempfile.mkstemp(dir=flavour_dir, prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(content)
        os.replace(tmp, target)
    except OSError as exc:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise HTTPException(507, f"Write failed: {exc}")

    f.image_type = "mermaid" if ext == ".mmd" else "file"
    f.image_value = file.filename
    from models.state import ChangeState
    if f.change == ChangeState.CLEAN:
        f.change = ChangeState.MODIFIED

    rel = f"infra/{product}/{size}/{flavour}/{file.filename}"
    return {"filename": file.filename, "path": rel}


def _get_flavour_or_404(product: str, size: str, flavour: str):
    state = state_store.get_state()
    p = state.products.get(product)
    s = p.sizes.get(size) if p else None
    f = s.flavours.get(flavour) if s else None
    if not f:
        raise HTTPException(404, "Flavour not found")
    return f


@router.get("/files/content/{product}/{size}/{flavour}")
def get_file_content(product: str, size: str, flavour: str):
    f = _get_flavour_or_404(product, size, flavour)
    if not f.image_value:
        raise HTTPException(404, "No image file set")
    path = REPO_ROOT / "infra" / product / size / flavour / f.image_value
    if not path.exists():
        return {"content": "", "filename": f.image_value}
    return {"content": path.read_text(encoding="utf-8"), "filename": f.image_value}


@router.get("/files/image/{product}/{size}/{flavour}")
def get_image_file(product: str, size: str, flavour: str):
    f = _get_flavour_or_404(product, size, flavour)
    if not f.image_value:
        raise HTTPException(404, "No image file set")
    path = REPO_ROOT / "infra" / product / size / flavour / f.image_value
    if not path.exists():
        raise HTTPException(404, "File not found on disk")
    return FileResponse(path)

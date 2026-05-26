from __future__ import annotations
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services import state_store
from routers import tree, products, adoc, files, units, git as git_router
from mcp_server.server import mcp


REPO_ROOT = Path(os.environ.get("REPO_ROOT", "."))


@asynccontextmanager
async def lifespan(app: FastAPI):
    products_json = REPO_ROOT / "infra" / "products.json"
    if not products_json.exists() or products_json.stat().st_size == 0:
        raise RuntimeError(f"infra/products.json not found at {products_json} — check REPO_ROOT")
    state_store.load_state(REPO_ROOT)
    yield


app = FastAPI(title="Infra Sizing Web Editor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tree.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(adoc.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(units.router, prefix="/api")
app.include_router(git_router.router, prefix="/api")
app.mount("/mcp", mcp.sse_app(mount_path="/mcp"))

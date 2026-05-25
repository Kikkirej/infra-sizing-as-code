from __future__ import annotations
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services import state_store
from routers import tree, products, adoc, files, units, git as git_router


REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parents[4]))


@asynccontextmanager
async def lifespan(app: FastAPI):
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

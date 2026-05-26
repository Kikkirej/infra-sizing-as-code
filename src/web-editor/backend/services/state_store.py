from __future__ import annotations
from pathlib import Path

from models.state import EditorState
from services.loader import load_infra

_state: EditorState | None = None


def load_state(repo_root: Path) -> None:
    global _state
    _state = load_infra(repo_root)


def get_state() -> EditorState:
    if _state is None:
        raise RuntimeError("EditorState not initialised — call load_state() first")
    return _state

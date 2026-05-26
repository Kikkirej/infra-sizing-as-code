import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.state import ChangeState, EditorState, UnitsNode
from services import state_store


@pytest.fixture
def empty_state():
    return EditorState(
        units=UnitsNode(units=["vCPU", "GB"], change=ChangeState.CLEAN),
    )


@pytest.fixture
def client(empty_state):
    state_store._state = empty_state
    from main import app
    return TestClient(app, raise_server_exceptions=True)

from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field


class ChangeState(str, Enum):
    CLEAN = "CLEAN"
    MODIFIED = "MODIFIED"
    ADDED = "ADDED"
    DELETED = "DELETED"
    ERROR = "ERROR"


class TypedValueNode(BaseModel):
    type: str
    unit: str
    value: float | None = None
    formula: str | None = None
    invalid: bool = False


class PartitionNode(BaseModel):
    size: TypedValueNode
    performance: str
    comment: str = ""


class ServerNode(BaseModel):
    system: str
    count: int = 1
    cpu: TypedValueNode
    cpu_clocking: str
    memory: TypedValueNode
    disk: list[PartitionNode] = []
    network: list[str] = []
    software: list[str] = []
    comment: str = ""
    change: ChangeState = ChangeState.CLEAN


class FlavourNode(BaseModel):
    shortname: str
    display_name: str
    image_type: str | None = None
    image_value: str | None = None
    change: ChangeState = ChangeState.CLEAN
    preamble_content: str = ""
    suffix_content: str = ""
    preamble_change: ChangeState = ChangeState.CLEAN
    suffix_change: ChangeState = ChangeState.CLEAN
    servers: list[ServerNode] = []


class SizeNode(BaseModel):
    shortname: str
    display_name: str
    prefix_text: str = ""
    suffix_text: str = ""
    change: ChangeState = ChangeState.CLEAN
    flavours: dict[str, FlavourNode] = {}


class ProductNode(BaseModel):
    shortname: str
    display_name: str
    change: ChangeState = ChangeState.CLEAN
    error: str | None = None
    preamble_content: str = ""
    suffix_content: str = ""
    preamble_change: ChangeState = ChangeState.CLEAN
    suffix_change: ChangeState = ChangeState.CLEAN
    sizes: dict[str, SizeNode] = {}


class UnitsNode(BaseModel):
    units: list[str] = []
    change: ChangeState = ChangeState.CLEAN


class EditorState(BaseModel):
    products: dict[str, ProductNode] = {}
    units: UnitsNode = Field(default_factory=UnitsNode)

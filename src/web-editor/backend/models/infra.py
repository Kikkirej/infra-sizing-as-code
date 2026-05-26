from __future__ import annotations
from typing import Literal, Union
from pydantic import BaseModel, Field


class StaticTypedValue(BaseModel):
    type: Literal["static"]
    unit: str
    value: float


class DynamicTypedValue(BaseModel):
    type: Literal["dynamic"]
    unit: str
    formula: str


TypedValue = Union[StaticTypedValue, DynamicTypedValue]


class Partition(BaseModel):
    size: TypedValue = Field(discriminator="type")
    performance: str
    comment: str = ""


class Server(BaseModel):
    system: str
    count: int = 1
    cpu: TypedValue = Field(discriminator="type")
    cpu_clocking: str
    memory: TypedValue = Field(discriminator="type")
    disk: list[Partition]
    network: list[str] = []
    software: list[str] = []
    comment: str = ""


class FlavourImage(BaseModel):
    type: Literal["file", "mermaid"]
    value: str


class Flavour(BaseModel):
    shortname: str
    display_name: str
    servers: list[Server] = []
    image: FlavourImage | None = None
    has_prefix: bool = False
    has_suffix: bool = False


class Size(BaseModel):
    shortname: str
    display_name: str
    flavours: list[Flavour] = []
    prefix_text: str = ""
    suffix_text: str = ""


class Product(BaseModel):
    shortname: str
    display_name: str
    sizes: list[Size] = []
    prefix: str = "prefix.adoc"
    suffix: str = "suffix.adoc"

from __future__ import annotations
import re
from pydantic import BaseModel, field_validator


_AUTHOR_TOKEN = re.compile(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*, [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*$")
_VERSION_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


def _validate_author(value: str) -> str:
    tokens = [t.strip() for t in value.split(";")]
    invalid = [t for t in tokens if not _AUTHOR_TOKEN.match(t)]
    if invalid:
        quoted = ", ".join(f"'{t}'" for t in invalid)
        raise ValueError(f"Invalid authors: {quoted}")
    return value


def _validate_version_name(value: str) -> str:
    if not _VERSION_NAME.match(value):
        raise ValueError(
            f"version_name {value!r} is invalid. "
            "Only alphanumeric characters, dots, hyphens, and underscores are allowed."
        )
    return value


class VersionEntry(BaseModel):
    author: str
    date: str
    notes: str | None = None

    @field_validator("author")
    @classmethod
    def validate_author(cls, v: str) -> str:
        return _validate_author(v)


class VersionFile(BaseModel):
    version_name: str
    entries: list[VersionEntry]

    @field_validator("version_name")
    @classmethod
    def validate_version_name(cls, v: str) -> str:
        if not v:
            return v
        return _validate_version_name(v)


class VersionNoteIn(BaseModel):
    product_shortname: str
    author: str
    date: str
    notes: str | None = None

    @field_validator("author")
    @classmethod
    def validate_author(cls, v: str) -> str:
        return _validate_author(v)

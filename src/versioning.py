from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class VersionEntryData:
    author: str
    date: str
    notes: str | None = None


@dataclass
class VersionFileData:
    version_name: str
    entries: list[VersionEntryData] = field(default_factory=list)

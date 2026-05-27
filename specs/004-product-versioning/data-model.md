# Data Model: Product Version Management

## Entity Hierarchy

```
Product
└── versioning/          (new subdirectory in infra/<shortname>/)
    ├── wip.json         → WIPVersion (mutable)
    └── <version>.json   → ReleasedVersion (immutable, 0..*)
```

## Entities

### VersionEntry

A single change record within a version file.

| Field    | Type             | Required | Constraints |
|----------|------------------|----------|-------------|
| `author` | string           | Yes      | One or more authors separated by `; `. Each token must match `^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*, [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*$` |
| `date`   | string (ISO 8601)| Yes      | Format: `YYYY-MM-DD`; stored as a string, displayed via date picker |
| `notes`  | string \| null   | No       | Free text; may be empty string or null |

`VersionEntry` does **not** carry a `version_name`. The `version_name` is a property of the containing `VersionFile`, shared across all entries.

---

### VersionFile (base shape for WIP and Released versions)

Represents the on-disk JSON structure of any version file.

| Field          | Type                  | Required | Constraints |
|----------------|-----------------------|----------|-------------|
| `version_name` | string                | Yes      | Matches `^[A-Za-z0-9._-]+$`; used as the filename for released versions and as part of the git tag |
| `entries`      | array of VersionEntry | Yes      | Ordered list (newest last); may be empty only in WIP; release requires at least one entry (FR-017) |

**WIPVersion** (`versioning/wip.json`): mutable; entries can be created, updated, deleted via CRUD API.

**ReleasedVersion** (`versioning/<version_name>.json`): immutable; created at release time from the WIP snapshot; read-only via the API.

---

### VersionNote (commit-time addition, not persisted as a separate entity)

Used only in the `POST /api/git/commit` request body to append an entry to a product's WIP version at commit time.

| Field               | Type   | Required | Constraints |
|---------------------|--------|----------|-------------|
| `product_shortname` | string | Yes      | Must match an existing product |
| `author`            | string | Yes      | Same validation as VersionEntry.author |
| `date`              | string | Yes      | ISO 8601 date |
| `notes`             | string | No       | Free text |

---

## On-Disk File Structure

```
infra/<shortname>/
└── versioning/
    ├── wip.json               # Active in-progress version
    └── <version_name>.json    # Released version (one file per release)
```

### Example `wip.json`

```json
{
  "version_name": "1.1.0",
  "entries": [
    {
      "author": "Jane, Smith",
      "date": "2026-05-26",
      "notes": "copied from previous version"
    },
    {
      "author": "John, Doe; Jane, Smith",
      "date": "2026-05-27",
      "notes": "Added HA configuration for application tier"
    }
  ]
}
```

### Example `1.0.0.json` (released)

```json
{
  "version_name": "1.0.0",
  "entries": [
    {
      "author": "John, Doe",
      "date": "2026-05-20",
      "notes": "Initial sizing for 500 concurrent users"
    }
  ]
}
```

---

## State Transitions

```
[no versioning/ folder]
        │  first CRUD write or release
        ▼
  wip.json (empty or with entries)
        │  release action (entries > 0)
        ▼
  <version>.json (immutable)  +  new wip.json (seeded)
```

- `wip.json` is the only mutable version file. It is always present after the first versioning interaction.
- Released files are written once and never modified. The API returns 405 Method Not Allowed for any mutating request on a released version.
- If `wip.json` is missing at read time, the panel shows an empty-state (with "Add Entry" available). If it is malformed, the panel shows an error state with a "Reset to empty WIP" option.

---

## Identity and Uniqueness Rules

- `version_name` is unique within a product: no two files in `versioning/` may share the same `version_name` value.
- Attempting to release with a `version_name` that already exists as `<version_name>.json` is blocked with HTTP 409 (FR-016).
- `version_name` is the stable identifier used in the git tag: `<product_shortname>-<version_name>`.
- Git tags are unique within a repository by definition; a duplicate tag attempt will be caught by GitPython and surfaced as an HTTP 409.

---

## Pydantic Models (backend)

Located in `src/web-editor/backend/models/versioning.py`.

```python
class VersionEntry(BaseModel):
    author: str    # validated by field_validator
    date: str      # YYYY-MM-DD
    notes: str | None = None

class VersionFile(BaseModel):
    version_name: str  # validated by field_validator
    entries: list[VersionEntry]

class VersionNoteIn(BaseModel):
    product_shortname: str
    author: str
    date: str
    notes: str | None = None
```

Validators:
- `version_name`: `re.fullmatch(r'^[A-Za-z0-9._-]+$', v)` — raise `ValueError` if no match.
- `author`: split on `;\s*`, validate each token with `re.fullmatch(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*, [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*$", token)` — on failure, raise `ValueError` listing all invalid tokens (FR-020).

---

## Shared Build-Pipeline Types (`src/versioning.py`)

Plain Python dataclasses used by `src/loader.py` and `src/renderer.py`. No Pydantic dependency — keeping the CLI build pipeline self-contained.

```python
@dataclass
class VersionEntryData:
    author: str
    date: str
    notes: str | None = None

@dataclass
class VersionFileData:
    version_name: str
    entries: list[VersionEntryData]
```

## Product Loader Extension (`src/loader.py`)

The existing `Product` dataclass gains:

```python
@dataclass
class Product:
    ...
    version_file: VersionFileData | None = None  # None if no versioning/ dir
```

`_load_product()` attempts to read `infra/<shortname>/versioning/wip.json` and deserialise it into `VersionFileData`. On parse error, `version_file` is set to `None` (the web editor panel detects and surfaces the error via the API; the CLI renderer logs a warning and skips the version table).

## Router Boundary Mapping

The web editor backend's Pydantic `VersionFile` (in `src/web-editor/backend/models/versioning.py`) maps to/from `VersionFileData` at the router boundary. The release endpoint reads `VersionFileData` from the loader and converts to `VersionFile` for response serialisation. No direct import exists between `src/loader.py` and the backend Pydantic models.

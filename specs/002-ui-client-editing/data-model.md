# Data Model: Infrastructure Sizing Web Editor

**Branch**: `002-ui-client-editing` | **Date**: 2026-05-25

---

## On-Disk JSON Schema

The web editor reads and writes the existing `infra/` directory layout. The schemas
below are authoritative; the editor MUST NOT introduce new fields or restructure files.

### `infra/products.json`
```json
[
  { "shortname": "acme-crm", "display_name": "ACME CRM Platform" }
]
```

### `infra/<product>/meta.json`
```json
{ "prefix": "prefix.adoc", "suffix": "suffix.adoc" }
```

### `infra/<product>/sizes.json`
```json
[
  { "shortname": "small",  "display_name": "Small (100 Users)" }
]
```

### `infra/<product>/<size>/meta.json`
```json
{ "prefix_text": "Designed for up to 100 users.", "suffix_text": "See Medium for larger." }
```

### `infra/<product>/<size>/flavours.json`
```json
[
  { "shortname": "appserver", "display_name": "Application Servers" }
]
```

### `infra/<product>/<size>/<flavour>/meta.json`
```json
{
  "image": { "type": "file", "value": "diagram.png" }
}
```
`image` is optional. `type` is `"file"` or `"mermaid"`. `value` is the filename within
the flavour directory.

### `infra/<product>/<size>/<flavour>/servers.json`
```json
[
  {
    "system": "Application Server",
    "count": 2,
    "cpu":    { "type": "static",  "value": 8,   "unit": "vCPU" },
    "cpu_clocking": "3.0 GHz",
    "memory": { "type": "static",  "value": 32,  "unit": "GB" },
    "disk": [
      { "size": { "type": "static", "value": 100, "unit": "GB" }, "performance": "NVMe SSD", "comment": "OS" }
    ],
    "network":  ["2× 10GbE"],
    "software": ["OpenJDK 17"],
    "comment":  "Active/active pair"
  }
]
```
Dynamic TypedValue example: `{ "type": "dynamic", "formula": "n * 4", "unit": "vCPU" }`

### `infra/units.json` *(new)*
```json
["vCPU", "GB", "GiB", "TB", "TiB", "GHz", "MHz"]
```
A flat JSON array of unit strings. Created with default seed if absent on editor startup.

### AsciiDoc files
- `infra/<product>/prefix.adoc` and `suffix.adoc` — product-level
- `infra/<product>/<size>/<flavour>/prefix.adoc` and `suffix.adoc` — flavour-level
- All are plain text; the editor reads/writes full file content without transformation.

---

## In-Memory State Model (Backend)

The backend holds a single `EditorState` instance (module-level singleton). All mutation
goes through this object; no file is written until commit.

### ChangeState (enum)

```
CLEAN    — matches on-disk state
MODIFIED — fields changed in memory, not yet committed
ADDED    — new entity created in memory, not yet written to disk
DELETED  — marked for deletion; removed from disk on next commit
ERROR    — failed to load from disk (malformed JSON); not editable
```

### EditorState

```
EditorState
├── products: dict[shortname → ProductNode]
└── units: UnitsNode
```

### ProductNode

```
ProductNode
├── shortname: str
├── display_name: str
├── change: ChangeState
├── error: str | None         # set if load failed (ChangeState.ERROR)
├── prefix_content: str     # full file content; empty string if file absent
├── suffix_content: str
├── prefix_change: ChangeState
├── suffix_change: ChangeState
└── sizes: dict[shortname → SizeNode]
```

### SizeNode

```
SizeNode
├── shortname: str
├── display_name: str
├── prefix_text: str
├── suffix_text: str
├── change: ChangeState
└── flavours: dict[shortname → FlavourNode]
```

### FlavourNode

```
FlavourNode
├── shortname: str
├── display_name: str
├── image: FlavourImage | None   # {type: "file"|"mermaid", value: str}
├── change: ChangeState
├── prefix_content: str
├── suffix_content: str
├── prefix_change: ChangeState
├── suffix_change: ChangeState
└── servers: list[ServerNode]
```

### ServerNode

```
ServerNode
├── system: str
├── count: int                  # default 1
├── cpu: TypedValueNode
├── cpu_clocking: str
├── memory: TypedValueNode
├── disk: list[PartitionNode]
├── network: list[str]
├── software: list[str]
├── comment: str
└── change: ChangeState
```

### TypedValueNode

```
TypedValueNode (discriminated union)
├── type: "static" | "dynamic"
├── unit: str                   # must exist in UnitsNode.units
├── value: float | None         # present when type = "static"
├── formula: str | None         # present when type = "dynamic"
└── invalid: bool               # true when unit was deleted from registry
```

### PartitionNode

```
PartitionNode
├── size: TypedValueNode
├── performance: str
└── comment: str
```

### UnitsNode

```
UnitsNode
├── units: list[str]
└── change: ChangeState
```

---

## Key Invariants

1. **Shortname uniqueness**: No two siblings (sizes within a product, flavours within a
   size) may share the same shortname, including nodes in DELETED state. The editor
   enforces this at write time with an inline validation error (FR-032).

2. **Unit reference integrity**: When a unit is deleted from `UnitsNode.units`, all
   `TypedValueNode` instances referencing that unit have `invalid = true`. The commit
   action is blocked until all invalid TypedValues are resolved (FR-026).

3. **Commit gate**: The commit is blocked if any of the following is true:
   - The git repository is in detached HEAD state (FR-034)
   - Any `TypedValueNode.invalid = true`
   - Any server has zero disk partitions (FR-019)
   - Any server has an empty `system` field (FR-019)

4. **DELETED node visibility**: Nodes with `ChangeState.DELETED` are retained in all
   in-memory dicts and included in tree API responses with `change: "DELETED"`. The
   frontend renders them with strikethrough and red color (FR-017a). They are excluded
   from validation (invariant 3) and from sibling uniqueness checks for new names.

5. **Atomic disk write order** (on commit):
   1. Write all modified `servers.json` files
   2. Write all modified `meta.json` files
   3. Write all modified registry files (`products.json`, `sizes.json`, `flavours.json`)
   4. Write all modified `.adoc` files
   5. Write `infra/units.json` if changed
   6. Delete directories for DELETED entities (leaf → root order)
   7. `git add -A infra/` → `git commit` → `git push`
   If any step fails, an error is returned; no rollback of already-written files (files
   are consistent with the intended new state). The git commit is only created after all
   files are written successfully.

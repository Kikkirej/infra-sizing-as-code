# Data Model: Infrastructure Sizing Document Export

**Phase 1 output** | **Branch**: `001-infra-sizing-doc-export` | **Date**: 2026-05-24

## Entity Overview

```
ProductRegistry (infra/products.json)
  └── Product (infra/{shortname}/)
        ├── ProductMeta (infra/{shortname}/meta.json)
        ├── SizeRegistry (infra/{shortname}/sizes.json)
        └── Size (infra/{shortname}/{size-shortname}/)
              ├── SizeMeta (infra/{shortname}/{size-shortname}/meta.json)
              ├── FlavourRegistry (infra/{shortname}/{size-shortname}/flavours.json)
              └── Flavour (infra/{shortname}/{size-shortname}/{flavour-shortname}/)
                    ├── FlavourMeta (…/meta.json)
                    └── ServerList (…/servers.json)
                          └── Server[]
                                └── Partition[]
```

---

## Entities

### TypedValue

**Used by**: `Server.cpu`, `Server.memory`, `Partition.size`

A typed quantity with a unit. The `type` field selects between a fixed value
and a formula-based dynamic value.

**Shape (static)**:
```json
{ "type": "static", "value": 8, "unit": "vCPU" }
```

**Shape (dynamic)**:
```json
{ "type": "dynamic", "formula": "n × 4", "unit": "vCPU" }
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | yes | `"static"` or `"dynamic"` |
| value | number | if static | Numeric quantity (integer or float) |
| formula | string | if dynamic | Human-readable expression (e.g. `"n × 4"`); rendered as-is in PDF |
| unit | string | yes | Unit label (e.g. `"vCPU"`, `"GB"`, `"TB"`) |

**Rendered form**:
- Static: `{value} {unit}` → `8 vCPU`, `32 GB`, `500 GB`
  - Integer values display without decimal: `8` not `8.0`
- Dynamic: `{formula} {unit}` → `n × 4 vCPU`, `n × 2 GB`

**Validation rules**:
- `type` must be `"static"` or `"dynamic"`
- `value` required and must be a positive number when `type == "static"`
- `formula` required and non-empty when `type == "dynamic"`
- `unit` required and non-empty in both cases

---

### ProductRegistry

**File**: `infra/products.json`

**Shape** (JSON array):
```json
[
  { "shortname": "product-a", "display_name": "Product A" },
  { "shortname": "product-b", "display_name": "Product B" }
]
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| shortname | string | yes | Folder name under `infra/`; no spaces; unique |
| display_name | string | yes | Human-readable name shown in PDF |

**Validation rules**:
- File must exist and be valid JSON (fatal if absent/malformed — FR-022)
- Array must not be empty
- All shortnames must be unique within the array
- Corresponding directory `infra/{shortname}/` must exist (FR-023)

---

### ProductMeta

**File**: `infra/{shortname}/meta.json`

**Shape**:
```json
{
  "prefix": "prefix.adoc",
  "suffix": "suffix.adoc"
}
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| prefix | string | yes | Relative path to product-specific prefix `.adoc` |
| suffix | string | yes | Relative path to product-specific suffix `.adoc` |

**Validation rules**:
- File must exist and be valid JSON
- Both referenced `.adoc` files must exist on disk relative to the product folder
  (FR-015a; product-level failure if absent)

---

### SizeRegistry

**File**: `infra/{product-shortname}/sizes.json`

**Shape** (JSON array):
```json
[
  { "shortname": "small", "display_name": "50 Users" },
  { "shortname": "large", "display_name": "500 Users" }
]
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| shortname | string | yes | Folder name under the product directory |
| display_name | string | yes | Size label shown in PDF (omitted if single size — FR-004) |

**Validation rules**:
- Must contain at least one entry (FR-003; product-level failure if empty)
- All shortnames unique within the array
- Corresponding directory must exist

---

### SizeMeta

**File**: `infra/{product-shortname}/{size-shortname}/meta.json`

**Shape**:
```json
{
  "prefix_text": "Optional text placed before infrastructure content.",
  "suffix_text": "Optional text placed after infrastructure content."
}
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| prefix_text | string | no | Text rendered before the flavour tables for this size |
| suffix_text | string | no | Text rendered after the flavour tables for this size |

**Validation rules**:
- File must exist and be valid JSON
- Both fields optional; absent or null treated as empty string

---

### FlavourRegistry

**File**: `infra/{product-shortname}/{size-shortname}/flavours.json`

**Shape** (JSON array):
```json
[
  { "shortname": "appserver", "display_name": "Application Server" },
  { "shortname": "dbserver", "display_name": "Database Server" }
]
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| shortname | string | yes | Directory name under the size directory |
| display_name | string | yes | Flavour heading shown in PDF |

**Validation rules**:
- Must contain at least one entry (FR-003; product-level failure if empty)
- All shortnames unique within the array
- Corresponding directory must exist

---

### FlavourMeta

**File**: `infra/{product-shortname}/{size-shortname}/{flavour-shortname}/meta.json`

**Shape** (image entry optional):
```json
{
  "image": {
    "type": "file",
    "value": "architecture.png"
  }
}
```

```json
{
  "image": {
    "type": "mermaid",
    "value": "diagram.mmd"
  }
}
```

```json
{}
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| image | object | no | Optional image entry; omit for no image |
| image.type | string | yes (if image present) | `"file"` or `"mermaid"` |
| image.value | string | yes (if image present) | Relative path within flavour directory |

**Validation rules**:
- File must exist and be valid JSON
- If image present: `type` must be `"file"` or `"mermaid"`
- If `type: file`: `value` path must exist relative to the flavour directory
- If `type: mermaid`: `value` must be a `.mmd` file path existing relative to
  the flavour directory

---

### ServerList

**File**: `infra/{product-shortname}/{size-shortname}/{flavour-shortname}/servers.json`

**Shape** (JSON array of Server objects):
```json
[
  {
    "system": "Web Server",
    "count": 3,
    "cpu": { "type": "static", "value": 4, "unit": "vCPU" },
    "cpu_clocking": "3.2 GHz",
    "memory": { "type": "static", "value": 32, "unit": "GB" },
    "disk": [
      {
        "size": { "type": "static", "value": 500, "unit": "GB" },
        "performance": "NVMe SSD",
        "comment": "OS + App"
      },
      {
        "size": { "type": "static", "value": 2, "unit": "TB" },
        "performance": "7200 RPM HDD"
      }
    ],
    "network": ["2× 10GbE", "1× 1GbE"],
    "software": ["NGINX 1.25", "Java 17"],
    "comment": "Primary web tier"
  }
]
```

**Dynamic value example** (CPU scales with cluster size):
```json
{
  "system": "Worker Node",
  "count": 1,
  "cpu": { "type": "dynamic", "formula": "n × 4", "unit": "vCPU" },
  "cpu_clocking": "3.0 GHz",
  "memory": { "type": "dynamic", "formula": "n × 8", "unit": "GB" },
  "disk": [
    {
      "size": { "type": "static", "value": 100, "unit": "GB" },
      "performance": "NVMe SSD",
      "comment": "OS"
    },
    {
      "size": { "type": "dynamic", "formula": "n × 500", "unit": "GB" },
      "performance": "NVMe SSD",
      "comment": "Data (per node)"
    }
  ],
  "network": [],
  "software": [],
  "comment": "Scale n = number of worker nodes"
}
```

**Validation rules**:
- Must contain at least one Server (FR-003; product-level failure if empty)
- Each Server must have at least one Partition in `disk` (FR-024)

---

### Server

**Source**: element of `servers.json` array

**Fields**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| system | string | yes | — | Purpose description; first table column |
| count | integer | no | 1 | Number of instances; must be ≥ 1 |
| cpu | TypedValue | yes | — | CPU quantity + unit (e.g. `8 vCPU`); merged with cpu_clocking in table |
| cpu_clocking | string | yes | — | Clock speed free-text (e.g. `"3.2 GHz"`); rendered in parentheses after cpu |
| memory | TypedValue | yes | — | Memory quantity + unit (e.g. `32 GB`) |
| disk | array | yes | — | List of Partition objects; min 1 (FR-024) |
| network | array\<string\> | no | [] | Network interfaces; empty → blank cell |
| software | array\<string\> | no | [] | Software components; empty → blank cell |
| comment | string | no | "" | Optional server-level note |

**Table column order** (rendered): System | CPU | Memory | Disk | Comment

**System cell rendering**:
- `count == 1`: `{system}` (no count annotation)
- `count > 1`: `{system} [{count}]` — e.g. `Application Server [3]`

**Comment cell rendering**: Network items and Software items are folded into the
Comment cell alongside the original comment text.
- Software items first, then network items (each as `* {item}` bullet)
- Original comment text appended after bullets (if non-empty)
- If all three are absent/empty: blank `a|` cell

**CPU column rendering**: CPU and CPU Clocking are always merged into a single column.
Format: `{cpu_rendered} ({cpu_clocking})`
- Static example: `8 vCPU (3.2 GHz)`
- Dynamic example: `n × 4 vCPU (3.0 GHz)`

---

### Partition

**Source**: element of `server.disk` array

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| size | TypedValue | yes | Storage quantity + unit (e.g. `{ "type": "static", "value": 500, "unit": "GB" }`) |
| performance | string | yes | Storage tier (free-text, e.g. "NVMe SSD") |
| comment | string | no | Optional label (e.g. "OS + App") |

**Rendered format — primary (nested table)** within Disk `a|` cell:
```asciidoc
[cols="3,3,3",options="header"]
!===
! Size ! Perform- +
ance ! Comment/ +
Usage
! 500 GB ! NVMe SSD ! OS + App
! 2 TB ! 7200 RPM HDD !
! n × 500 GB ! NVMe SSD ! Data (per node)
!===
```
Comment cell is blank when absent. `TypedValue.render()` produces the Size cell value.

**Rendered format — fallback** (if nested table layout is unacceptable after visual testing):
- Main Disk cell: `{total_storage} ({n} partitions)` — e.g. `1.6 TB (3 partitions)`
- Separate titled table after the server table: `.Partitions — {server.system}` with
  columns Size / Performance / Comment, using standard `|===` syntax.

See `research.md` § 3 for the full fallback AsciiDoc template.

---

## Python Internal Types

These are Python dataclasses (stdlib `dataclasses`) used by `loader.py` after
deserialising JSON. They mirror the JSON entities above.

```python
@dataclass
class TypedValue:
    type: str           # "static" | "dynamic"
    unit: str
    value: float = 0.0  # used when type == "static"
    formula: str = ""   # used when type == "dynamic"

    def render(self) -> str:
        if self.type == "static":
            v = int(self.value) if self.value == int(self.value) else self.value
            return f"{v} {self.unit}"
        return f"{self.formula} {self.unit}"

@dataclass
class Partition:
    size: TypedValue
    performance: str
    comment: str = ""

@dataclass
class Server:
    system: str
    cpu: TypedValue
    cpu_clocking: str
    memory: TypedValue
    disk: list[Partition]          # min 1
    count: int = 1
    network: list[str] = field(default_factory=list)
    software: list[str] = field(default_factory=list)
    comment: str = ""

@dataclass
class FlavourImage:
    type: str       # "file" | "mermaid"
    value: str      # relative path within flavour directory

@dataclass
class Flavour:
    shortname: str
    display_name: str
    servers: list[Server]          # min 1
    image: FlavourImage | None = None
    has_prefix: bool = False
    has_suffix: bool = False

@dataclass
class Size:
    shortname: str
    display_name: str
    flavours: list[Flavour]        # min 1
    prefix_text: str = ""
    suffix_text: str = ""

@dataclass
class Product:
    shortname: str
    display_name: str
    sizes: list[Size]              # min 1
    prefix_path: str = ""
    suffix_path: str = ""
```

---

## Validation Summary

| Check | Scope | Failure mode |
|-------|-------|--------------|
| `theme.yml` absent | Global | Fatal — halt entire build |
| `infra/products.json` absent or malformed | Global | Fatal — halt entire build |
| Product folder missing | Per product | Product fails, continue |
| Product has no sizes | Per product | Product fails, continue |
| Size has no flavours | Per product | Product fails, continue |
| Flavour has no servers | Per product | Product fails, continue |
| Server has empty disk list | Per product | Product fails, continue |
| Prefix/suffix file missing | Per product | Product fails, continue |
| asciidoctor-pdf non-zero exit | Per product | Product fails, continue |

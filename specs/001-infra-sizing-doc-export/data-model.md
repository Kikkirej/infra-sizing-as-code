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
  "preamble": "preamble.adoc",
  "suffix": "suffix.adoc"
}
```

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| preamble | string | yes | Relative path to product-specific preamble `.adoc` |
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
    "cpu": "4 vCPU",
    "cpu_clocking": "3.2 GHz",
    "memory": "32 GB",
    "disk": [
      { "size": "500 GB", "performance": "NVMe SSD", "comment": "OS + App" },
      { "size": "2 TB",   "performance": "7200 RPM HDD" }
    ],
    "network": ["2× 10GbE", "1× 1GbE"],
    "software": ["NGINX 1.25", "Java 17"],
    "comment": "Primary web tier"
  }
]
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
| cpu | string | yes | — | CPU specification (free-text) |
| cpu_clocking | string | yes | — | Clock speed (free-text) |
| memory | string | yes | — | Memory specification (free-text) |
| disk | array | yes | — | List of Partition objects; min 1 (FR-024) |
| network | array\<string\> | no | [] | Network interfaces; empty → blank cell |
| software | array\<string\> | no | [] | Software components; empty → blank cell |
| comment | string | no | "" | Optional server-level note |

**Table column order** (FR-006 / FR-007a):
System → Count → CPU → CPU Clocking → Memory → Disk → Network → Software → Comment

---

### Partition

**Source**: element of `server.disk` array

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| size | string | yes | Storage capacity (free-text, e.g. "500 GB") |
| performance | string | yes | Storage tier (free-text, e.g. "NVMe SSD") |
| comment | string | no | Optional label (e.g. "OS + App") |

**Rendered format** within Disk cell (AsciiDoc `a|` cell):
```
* 500 GB, NVMe SSD — OS + App
* 2 TB, 7200 RPM HDD
```
(comment omitted when absent)

---

## Python Internal Types

These are Python dataclasses (stdlib `dataclasses`) used by `loader.py` after
deserialising JSON. They mirror the JSON entities above.

```python
@dataclass
class Partition:
    size: str
    performance: str
    comment: str = ""

@dataclass
class Server:
    system: str
    cpu: str
    cpu_clocking: str
    memory: str
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
    has_preamble: bool = False
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
    preamble_path: str = ""
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
| Preamble/suffix file missing | Per product | Product fails, continue |
| asciidoctor-pdf non-zero exit | Per product | Product fails, continue |

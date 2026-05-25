# JSON File Format Contracts

**Phase 1 output** | **Branch**: `001-infra-sizing-doc-export`

All JSON files in the `infra/` hierarchy are loaded and validated by `src/loader.py`.
This document is the authoritative schema reference for every file the build reads.

---

## `infra/products.json` — Product Registry

**Fatal if absent or malformed** (FR-022).

```json
[
  {
    "shortname": "<string, required>",
    "display_name": "<string, required>"
  }
]
```

| Field | Type | Constraints |
|-------|------|------------|
| shortname | string | Non-empty; valid directory name; unique across array |
| display_name | string | Non-empty |

---

## `infra/{product}/meta.json` — Product Metadata

```json
{
  "preamble": "<relative path to .adoc, required>",
  "suffix": "<relative path to .adoc, required>"
}
```

| Field | Type | Constraints |
|-------|------|------------|
| preamble | string | Non-empty; path relative to product folder; file must exist |
| suffix | string | Non-empty; path relative to product folder; file must exist |

---

## `infra/{product}/sizes.json` — Size Registry

```json
[
  {
    "shortname": "<string, required>",
    "display_name": "<string, required>"
  }
]
```

| Field | Type | Constraints |
|-------|------|------------|
| shortname | string | Non-empty; valid directory name; unique across array |
| display_name | string | Non-empty |

Array must contain at least one entry.

---

## `infra/{product}/{size}/meta.json` — Size Metadata

```json
{
  "prefix_text": "<string, optional>",
  "suffix_text": "<string, optional>"
}
```

| Field | Type | Constraints |
|-------|------|------------|
| prefix_text | string \| absent | Optional; treated as `""` if absent or null |
| suffix_text | string \| absent | Optional; treated as `""` if absent or null |

---

## `infra/{product}/{size}/flavours.json` — Flavour Registry

```json
[
  {
    "shortname": "<string, required>",
    "display_name": "<string, required>"
  }
]
```

| Field | Type | Constraints |
|-------|------|------------|
| shortname | string | Non-empty; valid directory name; unique across array |
| display_name | string | Non-empty |

Array must contain at least one entry.

---

## `infra/{product}/{size}/{flavour}/meta.json` — Flavour Metadata

```json
{
  "image": {
    "type": "file | mermaid",
    "value": "<relative path within flavour directory>"
  }
}
```

The `image` key is optional. An empty object `{}` is valid.

| Field | Type | Constraints |
|-------|------|------------|
| image | object \| absent | Optional |
| image.type | string | Required if `image` present; must be `"file"` or `"mermaid"` |
| image.value | string | Required if `image` present; relative path from flavour dir; file must exist |

---

## TypedValue Schema (reusable)

Used for `Server.cpu`, `Server.memory`, and `Partition.size`.

**Static**:
```json
{ "type": "static", "value": 8, "unit": "vCPU" }
```

**Dynamic**:
```json
{ "type": "dynamic", "formula": "n × 4", "unit": "vCPU" }
```

| Field | Type | Required | Constraints |
|-------|------|----------|------------|
| type | string | yes | `"static"` or `"dynamic"` |
| value | number | if static | Positive number |
| formula | string | if dynamic | Non-empty string; rendered verbatim |
| unit | string | yes | Non-empty (e.g. `"vCPU"`, `"GB"`, `"TB"`) |

---

## `infra/{product}/{size}/{flavour}/servers.json` — Server Definitions

```json
[
  {
    "system": "<string, required>",
    "count": "<integer ≥ 1, optional, default 1>",
    "cpu": { "type": "static | dynamic", "value": "<number if static>", "formula": "<string if dynamic>", "unit": "<string>" },
    "cpu_clocking": "<string, required>",
    "memory": { "type": "static | dynamic", "value": "<number if static>", "formula": "<string if dynamic>", "unit": "<string>" },
    "disk": [
      {
        "size": { "type": "static | dynamic", "value": "<number if static>", "formula": "<string if dynamic>", "unit": "<string>" },
        "performance": "<string, required>",
        "comment": "<string, optional>"
      }
    ],
    "network": ["<string>"],
    "software": ["<string>"],
    "comment": "<string, optional>"
  }
]
```

**Server fields**:

| Field | Type | Required | Default | Constraints |
|-------|------|----------|---------|------------|
| system | string | yes | — | Non-empty; purpose description |
| count | integer | no | 1 | ≥ 1 |
| cpu | TypedValue | yes | — | See TypedValue schema above |
| cpu_clocking | string | yes | — | Non-empty free-text; rendered in parentheses after cpu |
| memory | TypedValue | yes | — | See TypedValue schema above |
| disk | array | yes | — | Min 1 Partition (FR-024) |
| network | array\<string\> | no | `[]` | May be absent or empty |
| software | array\<string\> | no | `[]` | May be absent or empty |
| comment | string | no | `""` | May be absent |

Array must contain at least one Server.

**Partition fields**:

| Field | Type | Required | Constraints |
|-------|------|----------|------------|
| size | TypedValue | yes | See TypedValue schema; unit typically `"GB"` or `"TB"` |
| performance | string | yes | Non-empty (e.g. `"NVMe SSD"`) |
| comment | string | no | May be absent; treated as `""` |

**Rendered table column order**:
`System | CPU | Memory | Disk | Comment`

- **System cell**: `{system}` when `count == 1`; `{system} [{count}]` when `count > 1`
- **CPU cell**: merges `cpu` and `cpu_clocking` → `{cpu.render()} ({cpu_clocking})`
- **Comment cell**: software items + network items (each as `* {item}` bullet) + original comment text
  — Network and Software columns are not rendered separately; their content is folded into Comment

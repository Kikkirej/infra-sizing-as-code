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

## `infra/{product}/{size}/{flavour}/servers.json` — Server Definitions

```json
[
  {
    "system": "<string, required>",
    "count": "<integer ≥ 1, optional, default 1>",
    "cpu": "<string, required>",
    "cpu_clocking": "<string, required>",
    "memory": "<string, required>",
    "disk": [
      {
        "size": "<string, required>",
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
| cpu | string | yes | — | Non-empty |
| cpu_clocking | string | yes | — | Non-empty |
| memory | string | yes | — | Non-empty |
| disk | array | yes | — | Min 1 Partition (FR-024) |
| network | array\<string\> | no | `[]` | May be absent or empty |
| software | array\<string\> | no | `[]` | May be absent or empty |
| comment | string | no | `""` | May be absent |

Array must contain at least one Server.

**Partition fields**:

| Field | Type | Required | Constraints |
|-------|------|----------|------------|
| size | string | yes | Non-empty (e.g. `"500 GB"`) |
| performance | string | yes | Non-empty (e.g. `"NVMe SSD"`) |
| comment | string | no | May be absent; treated as `""` |

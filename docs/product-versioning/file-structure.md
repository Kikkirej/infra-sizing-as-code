# Product Versioning — File Structure

## Directory Layout

```
infra/
└── <product-shortname>/
    └── versioning/
        ├── wip.json            ← mutable; current in-progress entries
        └── <version-name>.json ← immutable; written once on release
```

Example with product `acme-crm` that has released version `1.0.0`:

```
infra/
└── acme-crm/
    └── versioning/
        ├── wip.json
        └── 1.0.0.json
```

The `versioning/` directory is created automatically on first use (either via the web editor or the `POST /api/products/{shortname}/versioning/wip/reset` endpoint).

---

## wip.json Schema

```json
{
  "version_name": "1.1.0",
  "entries": [
    {
      "author": "Smith, John",
      "date": "2026-05-15",
      "notes": "Initial setup"
    },
    {
      "author": "Smith, John; Doe, Jane",
      "date": "2026-05-26",
      "notes": "Added high-availability flavour"
    }
  ]
}
```

| Field | Type | Validation | Notes |
|-------|------|-----------|-------|
| `version_name` | string | `^[A-Za-z0-9._-]+$` or empty string | Empty string is allowed while drafting; must be set before release |
| `entries` | array | — | Ordered newest-last |
| `entries[].author` | string | Per-token: `^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*, [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*$`; tokens split on `;\s*` | Supports accented characters and hyphenated surnames |
| `entries[].date` | string | ISO 8601 date (YYYY-MM-DD) | Not validated beyond string type at storage; enforce in UI |
| `entries[].notes` | string or null | — | Optional free-text description |

---

## Released Version File Schema

Released version files (`<version-name>.json`) have the same structure as `wip.json` but with the version_name guaranteed to be set and entries frozen at the time of release.

```json
{
  "version_name": "1.0.0",
  "entries": [
    {
      "author": "Smith, John",
      "date": "2026-05-15",
      "notes": "Initial release"
    }
  ]
}
```

| Constraint | Value |
|-----------|-------|
| File name | Must equal `version_name` with `.json` appended |
| Mutability | Write-once; the release endpoint will refuse to overwrite |
| Ordering | Entries are newest-last (same as wip.json) |

---

## Version Name Validation Rules

`version_name` must match `^[A-Za-z0-9._-]+$`:

| Allowed characters | Examples |
|-------------------|---------|
| Alphanumeric | `1.0.0`, `v2`, `release3` |
| Dots | `1.0.0`, `2024.05` |
| Hyphens | `1.0-beta`, `v1-rc1` |
| Underscores | `1_0_0`, `release_2024` |

Empty string is allowed in `wip.json` (draft state) but **not** at release time.

---

## Git Tag Naming

On release, a git tag is created with the form:

```
<product-shortname>-<version-name>
```

For example, releasing version `1.0.0` of product `acme-crm` creates tag `acme-crm-1.0.0`.

---

## Rendered Output

When a product has a `versioning/wip.json` with at least one entry, the CLI build pipeline (`src/loader.py` + `src/renderer.py`) includes a **Version History** section in the generated AsciiDoc document:

```asciidoc
== Version History

[cols="15,15,30,40",options="header"]
|===
| Version | Date | Author(s) | Notes
| 1.0.0 | 2026-05-15 | Smith, John | Initial release
|===
```

This section is appended after the global suffix include. It is absent if `wip.json` does not exist.

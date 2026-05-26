# API Contracts: Product Versioning

All endpoints are prefixed with `/api` and mounted in the existing FastAPI app.

---

## List Versions

`GET /api/products/{shortname}/versioning`

Returns all available version identifiers for a product, sorted with WIP first.

**Response 200**:
```json
{
  "wip": true,
  "versions": ["1.0.0", "0.9.0"]
}
```

- `wip`: `true` if `versioning/wip.json` exists for this product.
- `versions`: list of `version_name` strings for released versions, newest-first (sorted by file mtime descending).

**Response 404**: Product not found.

---

## Get Version File

`GET /api/products/{shortname}/versioning/{version}`

- `{version}` is either `"wip"` or a released `version_name` (e.g., `"1.0.0"`).

**Response 200**:
```json
{
  "version_name": "1.0.0",
  "entries": [
    { "author": "Jane, Smith", "date": "2026-05-26", "notes": "Initial version" }
  ],
  "readonly": false
}
```

- `readonly`: `false` for WIP, `true` for released versions.

**Response 404**: Product or version not found.

**Response 422** (malformed `wip.json`):
```json
{ "detail": "wip.json is malformed or has an unexpected structure. Use POST /versioning/wip/reset to create a fresh WIP." }
```

---

## Reset Malformed WIP

`POST /api/products/{shortname}/versioning/wip/reset`

Replaces `versioning/wip.json` with a fresh, empty `VersionFile`. The `version_name` is set to an empty string; the user must update it before releasing.

**Response 200**:
```json
{ "version_name": "", "entries": [], "readonly": false }
```

**Response 404**: Product not found.

---

## Update WIP `version_name`

`PATCH /api/products/{shortname}/versioning/wip`

Body:
```json
{ "version_name": "1.1.0" }
```

**Response 200**:
```json
{ "version_name": "1.1.0" }
```

**Response 422**: `version_name` fails `^[A-Za-z0-9._-]+$` validation.

**Response 404**: Product not found or `wip.json` missing.

**Response 405**: Attempted on a released version (not applicable to this endpoint, but enforced at router level — released version names are immutable).

---

## Create Version Entry (WIP only)

`POST /api/products/{shortname}/versioning/wip/entries`

Body:
```json
{ "author": "Jane, Smith; John, Doe", "date": "2026-05-26", "notes": "HA configuration added" }
```

- `notes` is optional.

**Response 201**:
```json
{ "index": 1, "entry": { "author": "Jane, Smith; John, Doe", "date": "2026-05-26", "notes": "HA configuration added" } }
```

**Response 422**: Author validation fails — lists each invalid author token:
```json
{ "detail": "Invalid authors: 'JohnDoe', 'Jane'" }
```

**Response 404**: Product not found or `wip.json` missing.

---

## Update Version Entry (WIP only)

`PUT /api/products/{shortname}/versioning/wip/entries/{index}`

Body: same shape as POST (all fields required).

**Response 200**: Updated entry object.

**Response 404**: Product, WIP, or index not found.

**Response 422**: Validation failure (same format as POST).

---

## Delete Version Entry (WIP only)

`DELETE /api/products/{shortname}/versioning/wip/entries/{index}`

**Response 200**:
```json
{ "deleted": true }
```

**Response 404**: Product, WIP, or index not found.

---

## Release Product

`POST /api/products/{shortname}/release`

Body:
```json
{ "new_version_name": "1.1.0" }
```

Sequence (see plan.md — Implementation Notes):
1. Validate `wip.json` is present, valid, and non-empty.
2. Check `<version_name>.json` does not already exist.
3. Write `<version_name>.json`.
4. Regenerate `.adoc` and attempt PDF build.
5. Write new `wip.json` with seeded entry.
6. Commit + tag.

**Response 200**:
```json
{
  "version_name": "1.0.0",
  "tag": "acme-crm-1.0.0",
  "commit_sha": "a1b2c3d",
  "pdf_generated": true,
  "new_wip_version_name": "1.1.0"
}
```

**Response 422 — empty WIP**:
```json
{ "detail": "Cannot release a version with no change entries." }
```

**Response 409 — version already exists**:
```json
{ "detail": "Version 1.0.0 already exists. Please change the WIP version name." }
```

**Response 422 — invalid WIP `version_name`**:
```json
{ "detail": "version_name '1.0 0' is invalid. Only alphanumeric characters, dots, hyphens, and underscores are allowed." }
```

**Response 422 — invalid `new_version_name`**:
```json
{ "detail": "new_version_name '1.1 0' is invalid. Only alphanumeric characters, dots, hyphens, and underscores are allowed." }
```

**Response 404**: Product not found.

---

## Commit with Version Notes (extension to existing endpoint)

`POST /api/git/commit`

Extended body (new optional field):
```json
{
  "message": "Add HA config for acme-crm",
  "push": true,
  "version_notes": [
    {
      "product_shortname": "acme-crm",
      "author": "Jane, Smith",
      "date": "2026-05-26",
      "notes": "HA configuration added"
    }
  ]
}
```

- `version_notes` is optional; omitting it or passing an empty array preserves existing commit behaviour.
- Each note is appended to the corresponding product's `wip.json` **before** `write_all()`. If validation fails for any note, the commit is blocked with HTTP 422 listing the failing notes.
- Notes for products with no pending sizing changes are accepted (a version note can be added on any commit).

**Response** (unchanged): `{ "commit_sha": "a1b2c3d", "pushed": true }`

**Response 422 — invalid note**:
```json
{ "detail": "version_notes[0]: Invalid authors: 'JohnDoe'" }
```

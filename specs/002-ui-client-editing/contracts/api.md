# REST API Contract: Infrastructure Sizing Web Editor

**Branch**: `002-ui-client-editing` | **Date**: 2026-05-25

Base URL: `http://localhost:8000` (FastAPI backend)

All endpoints return `application/json`. Error responses: `{"detail": "<message>"}` with
appropriate HTTP status code.

---

## Tree & Overview

### `GET /api/tree`
Returns the full in-memory tree including change states.

**Response** `200`:
```json
{
  "products": {
    "acme-crm": {
      "shortname": "acme-crm",
      "display_name": "ACME CRM Platform",
      "change": "CLEAN",
      "error": null,
      "has_prefix": true,
      "has_suffix": true,
      "prefix_change": "CLEAN",
      "suffix_change": "CLEAN",
      "sizes": {
        "small": {
          "shortname": "small",
          "display_name": "Small (100 Users)",
          "change": "CLEAN",
          "flavours": {
            "appserver": {
              "shortname": "appserver",
              "display_name": "Application Servers",
              "change": "MODIFIED",
              "has_prefix": false,
              "has_suffix": false,
              "servers": [{ "system": "Application Server", "change": "MODIFIED" }]
            }
          }
        }
      }
    }
  }
}
```

### `GET /api/overview`
Returns product summary counts reflecting current in-memory state (FR-005).

**Response** `200`:
```json
{
  "products": [
    {
      "shortname": "acme-crm",
      "display_name": "ACME CRM Platform",
      "size_count": 3,
      "flavour_count": 7,
      "server_count": 14,
      "has_error": false
    }
  ]
}
```
Counts include ADDED nodes and exclude DELETED nodes.

---

## Products

### `GET /api/products/{shortname}`
Returns full product data (all sizes, flavours, servers with field values).

**Response** `200`: full ProductNode with all nested data.
**Response** `404`: product not found.

### `POST /api/products`
Add a new product.

**Request body**:
```json
{ "shortname": "new-product", "display_name": "New Product" }
```
**Response** `201`: created ProductNode (ADDED state, empty sizes).
**Response** `409`: shortname already exists.
**Response** `422`: validation error (empty shortname or display_name).

### `PUT /api/products/{shortname}`
Update product metadata.

**Request body**:
```json
{ "display_name": "Updated Name" }
```
`shortname` is immutable after creation (rename = delete + add).
**Response** `200`: updated ProductNode.
**Response** `404`: product not found.

### `DELETE /api/products/{shortname}`
Mark product as DELETED in memory.

**Response** `200`: `{ "change": "DELETED" }`
**Response** `404`: product not found.

### `POST /api/products/{shortname}/reset`
Reset product to on-disk state, discarding all in-memory changes for this product.

**Response** `200`: reloaded ProductNode (CLEAN state).
**Response** `404`: product not found on disk.

---

## Sizes

### `GET /api/products/{product}/sizes/{shortname}`
**Response** `200`: full SizeNode with all flavours and servers.
**Response** `404`.

### `POST /api/products/{product}/sizes`
```json
{ "shortname": "enterprise", "display_name": "Enterprise", "prefix_text": "", "suffix_text": "" }
```
**Response** `201`: SizeNode (ADDED).
**Response** `409`: shortname conflict within product.

### `PUT /api/products/{product}/sizes/{shortname}`
```json
{ "display_name": "...", "prefix_text": "...", "suffix_text": "..." }
```
**Response** `200`: updated SizeNode.

### `DELETE /api/products/{product}/sizes/{shortname}`
**Response** `200`: `{ "change": "DELETED" }`

---

## Flavours

### `GET /api/products/{product}/sizes/{size}/flavours/{shortname}`
**Response** `200`: full FlavourNode with servers.

### `POST /api/products/{product}/sizes/{size}/flavours`
```json
{ "shortname": "cacheserver", "display_name": "Cache Servers" }
```
**Response** `201`: FlavourNode (ADDED, empty servers list).
**Response** `409`: shortname conflict within size.

### `PUT /api/products/{product}/sizes/{size}/flavours/{shortname}`
```json
{ "display_name": "...", "image": { "type": "file", "value": "diagram.png" } }
```
`image` may be `null` to clear the image reference.
**Response** `200`: updated FlavourNode.

### `DELETE /api/products/{product}/sizes/{size}/flavours/{shortname}`
**Response** `200`: `{ "change": "DELETED" }`

### `POST /api/products/{product}/sizes/{size}/flavours/{shortname}/copy`
Deep-copy flavour (and all servers) to a target parent.

**Request body**:
```json
{
  "target_product": "acme-crm",
  "target_size": "medium"
}
```
Auto-appends `-copy` (then `-copy-2`, etc.) if shortname conflicts at target.
**Response** `201`: new FlavourNode at target (ADDED state).
**Response** `422`: incompatible target (target_size does not exist).

---

## Servers

### `GET /api/products/{product}/sizes/{size}/flavours/{flavour}/servers`
**Response** `200`: `{ "servers": [ <ServerNode>, ... ] }`

### `POST /api/products/{product}/sizes/{size}/flavours/{flavour}/servers`
Add a server. Body: full Server object (see data-model.md). Index is assigned by backend.
**Response** `201`: `{ "index": 2, "server": <ServerNode> }`

### `PUT /api/products/{product}/sizes/{size}/flavours/{flavour}/servers/{index}`
Replace server at index. Body: full Server object.
**Response** `200`: updated ServerNode.
**Response** `404`: index out of range.

### `DELETE /api/products/{product}/sizes/{size}/flavours/{flavour}/servers/{index}`
**Response** `200`: `{ "change": "DELETED" }`

---

## AsciiDoc Files

### `GET /api/adoc/{path:path}`
Read `.adoc` file content. `path` is relative to repo root, e.g.
`infra/acme-crm/prefix.adoc`.

**Response** `200`:
```json
{ "path": "infra/acme-crm/prefix.adoc", "content": "= Prefix\n...", "change": "CLEAN" }
```
`content` is empty string if file does not yet exist (ADDED state).

### `PUT /api/adoc/{path:path}`
Update adoc content in memory.

**Request body**:
```json
{ "content": "= Updated Prefix\n..." }
```
**Response** `200`: `{ "path": "...", "change": "MODIFIED" }`

---

## File Upload

### `POST /api/files/upload/{product}/{size}/{flavour}`
Upload a binary file (PNG, SVG, or `.mmd`) to the flavour directory. Written immediately
to disk (not deferred). Atomic write (FR-022a).

**Request**: `multipart/form-data` with field `file`.
**Allowed types**: `image/png`, `image/svg+xml`, `.mmd` (MIME: `text/plain`).

**Response** `200`:
```json
{ "filename": "diagram.png", "path": "infra/acme-crm/small/appserver/diagram.png" }
```
**Response** `422`: unsupported file type.
**Response** `507`: disk full or write error — no partial file left on disk.

---

## Units Registry

### `GET /api/units`
**Response** `200`:
```json
{ "units": ["vCPU", "GB", "GiB", "TB", "TiB", "GHz", "MHz"], "change": "CLEAN" }
```

### `POST /api/units`
Add a unit.
```json
{ "unit": "PiB" }
```
**Response** `201`: updated units list.
**Response** `409`: unit already exists.

### `DELETE /api/units/{unit}`
Delete a unit. Returns affected entities for warning display (FR-026).

**Response** `200`:
```json
{
  "unit": "GB",
  "affected_count": 5,
  "affected_paths": [
    "acme-crm / small / appserver / server[0].cpu",
    "acme-crm / small / dbserver / server[0].memory"
  ],
  "change": "MODIFIED"
}
```
The unit is removed from the registry and all referencing TypedValues are marked `invalid: true`.
The frontend MUST display the `affected_paths` in a warning before calling this endpoint.

---

## Git Operations

### `GET /api/git/status`
**Response** `200`:
```json
{
  "branch": "002-ui-client-editing",
  "is_detached": false,
  "has_remote": true,
  "remote_name": "origin"
}
```

### `GET /api/git/changes`
Returns the flat list of changed entity/file names for the pre-commit overview (FR-027a).

**Response** `200`:
```json
{
  "changes": [
    "acme-crm / small / appserver",
    "acme-crm / prefix.adoc",
    "new-product",
    "acme-erp / enterprise / dbserver"
  ],
  "count": 4
}
```

### `POST /api/git/commit`
Write all in-memory changes to disk, create a git commit, and push.

**Request body**:
```json
{ "message": "Add new-product sizing" }
```

**Response** `200`:
```json
{ "commit_sha": "abc1234", "pushed": true }
```
**Response** `409` (detached HEAD):
```json
{ "detail": "Repository is in detached HEAD state. Run 'git checkout <branch>' before committing." }
```
**Response** `422` (validation failures):
```json
{ "detail": "Commit blocked: 2 TypedValues have invalid units; 1 server has no disk partitions." }
```
**Response** `500` (push failed after commit):
```json
{
  "detail": "Commit created (abc1234) but push failed: Permission denied (publickey).",
  "commit_sha": "abc1234",
  "push_failed": true
}
```
When `push_failed: true`, the frontend displays a "Retry Push" button.

### `POST /api/git/push`
Retry push after a failed push. No body required.

**Response** `200`: `{ "pushed": true }`
**Response** `500`: `{ "detail": "Push failed: <reason>", "push_failed": true }`

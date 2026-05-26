# Infrastructure Sizing Web Editor — Overview

## Purpose

The web editor provides a browser-based UI for editing the `infra/` directory structure without requiring direct filesystem or YAML/JSON knowledge. Operators launch it locally via Docker Compose, make changes, and commit + push directly from the UI.

## Architecture

```
┌──────────────────────────────────┐
│  Browser (Vue 3 + Pinia)         │
│  Vite dev server  :5173          │
│  /api  →  proxy  → :8000         │
└───────────────┬──────────────────┘
                │ HTTP/REST
┌───────────────▼──────────────────┐
│  FastAPI backend  :8000          │
│  In-memory EditorState           │
│  GitPython (commit + push)       │
└───────────────┬──────────────────┘
                │ bind-mount
┌───────────────▼──────────────────┐
│  Host filesystem                 │
│  ./infra/  (read + write)        │
│  ./.git/   (read-only)           │
└──────────────────────────────────┘
```

**Backend** (`src/web-editor/backend/`): Python 3.11 + FastAPI 0.111 + Pydantic v2. Loads the entire `infra/` tree into an in-memory `EditorState` singleton on startup. All mutations go through the state; files are only written on commit.

**Frontend** (`src/web-editor/frontend/`): Vue.js 3.4 + Vite 5 + Pinia 2. Two-panel layout (tree sidebar + detail editor). Asciidoctor.js for in-browser AsciiDoc preview.

**Docker Compose** (`docker-compose.yml` at repo root): Two services — `backend` and `frontend`. SSH agent socket is forwarded into the backend container for authenticated `git push`.

## `infra/` File Structure

The editor manages the existing `infra/` layout and adds one new file:

```
infra/
  units.json                        ← NEW: flat array of allowed unit strings
  products.json                     ← registry of product shortnames
  {product}/
    meta.json                       ← display_name, optional prefix/suffix adoc paths
    sizes.json                      ← registry of size shortnames for this product
    flavours.json                   ← registry of flavour shortnames for this product
    {size}/
      {flavour}/
        servers.json                ← array of Server objects
        *.png / *.svg / *.mmd       ← flavour architecture image (optional)
        *.adoc                      ← AsciiDoc content files
```

`units.json` is seeded with defaults (`["vCPU","GB","GiB","TB","TiB","GHz","MHz"]`) when the file is absent. It is committed via the normal commit flow.

## Change State Model

Every node in the in-memory tree carries a `change` field:

| State      | Meaning                                   | Visual |
|------------|-------------------------------------------|--------|
| `CLEAN`    | Matches committed state                   | —      |
| `MODIFIED` | Field(s) edited, not yet committed        | Blue dot |
| `ADDED`    | Created in editor, not yet committed      | Green badge |
| `DELETED`  | Marked for deletion, not yet committed    | Strikethrough + red |
| `ERROR`    | File could not be loaded on startup       | Warning icon |

Deleted nodes remain visible in the tree until the next commit.

## Design Decisions

- **Atomic writes**: All file writes use `tempfile.mkstemp` + `os.replace` (POSIX-atomic) to prevent corrupt state on crash.
- **Write-on-commit only**: Files are never written speculatively; `write_all()` is called only immediately before `git commit`.
- **Units registry**: A single `units.json` registry enforces consistent unit strings across all `TypedValue` fields. Deleting a unit marks all referencing values as `invalid`.
- **Push retry**: If `git push` fails after a successful local commit, the backend returns `push_failed: true` plus the `commit_sha`. The UI shows a "Retry Push" button.
- **SSH agent forwarding**: The backend container receives the host SSH agent via `${SSH_AUTH_SOCK}:/ssh-agent` so `git push` to remote works without embedding credentials.

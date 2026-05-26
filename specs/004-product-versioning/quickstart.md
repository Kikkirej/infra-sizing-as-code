# Quickstart: Product Version Management

## What's being built

Per-product version history management in the web editor. Version data lives in `infra/<product>/versioning/` as JSON files. The web editor gains a "Versions" tree node per product, a CRUD table for change entries, and a release flow that creates a named version file, a git tag, and a seeded new WIP version. The commit panel gains an optional per-product version note prompt.

## New files

```text
src/web-editor/backend/
├── models/
│   └── versioning.py              # VersionEntry, VersionFile, VersionNoteIn Pydantic models
├── routers/
│   └── versioning.py              # Version CRUD + release endpoint
└── tests/
    └── test_versioning.py         # Full coverage: CRUD, release, validation, edge cases

src/web-editor/frontend/src/
├── components/edit/
│   └── VersioningPanel.vue        # Version selector + version_name field + entry table
└── stores/
    └── versioning.js              # Pinia store: version list, selected version, entries

docs/product-versioning/
├── overview.md                    # Feature description and release workflow
└── file-structure.md              # versioning/ directory layout and JSON schemas
```

## Modified files

```text
src/
├── loader.py                      # Add version_file: VersionFile | None to Product dataclass
└── renderer.py                    # Add render_version_table(); append == Version History section

src/web-editor/backend/
├── main.py                        # Include versioning router
└── routers/git.py                 # Extend CommitBody with optional version_notes list

src/web-editor/frontend/src/
├── components/
│   ├── TreePanel.vue              # Add "Versions" leaf node under each product
│   ├── MainPanel.vue              # Add <VersioningPanel> for type === 'versions'
│   ├── CommitPanel.vue            # Add per-product version note prompt step
│   └── edit/ProductEdit.vue       # Add "Release" button + release popup modal
```

## Key design decisions (from research.md)

- **Version files in `infra/`**: `infra/<shortname>/versioning/wip.json` and `infra/<shortname>/versioning/<version_name>.json`. Git-tracked alongside sizing data.
- **Release is a REST endpoint**: `POST /api/products/{shortname}/release` handles the full release sequence (validate → write file → regenerate adoc → attempt PDF → seed new wip.json → commit → tag). The UI collects `new_version_name` in a popup before calling it.
- **Renderer reads from loader**: `src/loader.py` loads `versioning/wip.json` into `Product.version_file`; `src/renderer.py` appends a `== Version History` AsciiDoc section when present. This means the CLI `build.py` also includes version history automatically.
- **Commit-time notes via extended commit endpoint**: The existing `POST /api/git/commit` body accepts an optional `version_notes` array. Notes are appended to `wip.json` files before `write_all()` — same atomic transaction as the commit.
- **Author validation on both sides**: Regex `^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*, [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*$` per author token; multi-author split on `;\s*`. Enforced in Vue reactive input (frontend) and Pydantic `field_validator` (backend). On multi-author failure, all invalid tokens are listed in the error.
- **Immutable released versions**: Released version files are read-only. The API returns 405 for any mutating request targeting a released version. The frontend hides CRUD controls and `version_name` edit when a released version is selected.

## Running locally

No new dependencies or configuration required. Start the stack as usual:

```bash
docker compose up
# or without Docker:
cd src/web-editor/backend
REPO_ROOT=$(pwd)/../../.. uvicorn main:app --reload --port 8000
```

The new `/api/products/{shortname}/versioning` endpoints are available once the backend starts.

## Testing

Backend:
```bash
cd src/web-editor/backend
pytest tests/test_versioning.py -v
```

Key test cases:
- CRUD operations on WIP entries (create, read, update, delete)
- Author validation: valid single, valid multi, invalid single, mixed valid/invalid
- `version_name` validation: valid patterns, invalid characters
- Release: happy path, empty WIP blocked, duplicate version blocked, malformed WIP handled
- Commit with version notes: valid note appended, invalid note blocks commit
- Reset malformed WIP

Frontend (vitest):
```bash
cd src/web-editor/frontend
npm run test:unit
```

## Example: First-time versioning setup

```
1. Open product "acme-crm" in the web editor
2. Click "Versions" in the product tree
   → Empty state shown with "Add Entry" button
3. Click "Add Entry"
   → Fill: Author = "John, Doe", Date = 2026-05-26, Notes = "Initial sizing"
4. Entry saved to infra/acme-crm/versioning/wip.json
5. Set version_name field to "1.0.0"
6. Click "Release" on the product panel
   → Popup: "Enter new WIP version name" → type "1.1.0" → Confirm
7. Backend: writes 1.0.0.json, creates tag acme-crm-1.0.0, seeds new wip.json
```

## File-structure reference

See `docs/product-versioning/file-structure.md` for the full directory layout and annotated JSON schemas.

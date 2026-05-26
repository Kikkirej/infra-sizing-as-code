# Implementation Plan: Product Version Management

**Branch**: `004-product-versioning` | **Date**: 2026-05-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-product-versioning/spec.md`

## Summary

Add per-product version history management to the web editor. Version data is stored in `infra/<product>/versioning/` as JSON files (`wip.json` for the active version; `<version_name>.json` for each released version). The frontend gains a "Versions" tree entry per product with a CRUD table, a version selector, and a shared `version_name` field. A new backend release endpoint finalises the WIP version: it writes the named version file, regenerates the product's `.adoc` (including a version-history table), attempts PDF conversion, commits all changes, and creates a git tag. The commit panel gains an optional per-product version-note prompt.

## Technical Context

**Language/Version**: Python 3.11 (backend); JavaScript / Vue 3.4 (frontend)

**Primary Dependencies**: FastAPI 0.111, Pydantic 2.7, GitPython 3.1.43 (backend — all existing); Vue 3.4, Pinia 2.1, Axios 1.7, Vite 5 (frontend — all existing). No new dependencies required.

**Storage**: File system — `infra/<product>/versioning/` directory (new per-product subdirectory); JSON files read and written directly to disk at request time; no in-memory caching.

**Testing**: pytest + httpx (backend existing); vitest (frontend existing)

**Target Platform**: Linux server (Docker) + local dev

**Project Type**: Extension to existing FastAPI web service + Vue 3 SPA

**Performance Goals**: CRUD entry operations < 30 s (SC-001); commit prompt skip adds < 2 s to commit flow (SC-005)

**Constraints**:
- No new Python or JS package dependencies
- All version state stored in Git-tracked `infra/` tree (constitution principle I)
- Release endpoint operates synchronously; PDF build is attempted and fails gracefully if asciidoctor is unavailable at runtime
- Author validation enforced on both frontend (immediate feedback) and backend (authoritative); regex `^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*, [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*$` per author token (semicolon-separated)
- `version_name` validation: `^[A-Za-z0-9._-]+$`

**Scale/Scope**: Local/internal single-user; no concurrent-write protection required for v1

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git as Single Source of Truth | ✅ Pass | All version data in `infra/<product>/versioning/` under Git; git tags are first-class Git artifacts created at release time |
| II. File-First Architecture | ✅ Pass | New backend code in `src/web-editor/backend/`; new frontend components in `src/web-editor/frontend/src/`; docs in `docs/product-versioning/` |
| III. Infrastructure as Code | ✅ Pass | No new infra definitions; version JSON files are data in the existing `infra/` tree |
| IV. CI/CD Portability | ✅ Pass | No new dependencies; Python and JS source changes are picked up by both existing CI pipelines automatically |
| V. Documentation-Driven Development | ✅ Pass | `docs/product-versioning/overview.md` and `docs/product-versioning/file-structure.md` delivered as part of this feature |

No gate violations. No Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/004-product-versioning/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── versioning-api.md  # Phase 1 output — REST API contracts
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
# New backend files
src/web-editor/backend/
├── models/
│   └── versioning.py          # New: VersionEntry, VersionFile Pydantic models
├── routers/
│   └── versioning.py          # New: version CRUD + release endpoint
└── tests/
    └── test_versioning.py     # New: full coverage of CRUD + release + validation

# Modified backend files
src/web-editor/backend/
├── main.py                    # Modified: include versioning router
└── routers/
    └── git.py                 # Modified: commit body accepts optional version_notes list

# Modified build pipeline (renderer + loader)
src/
├── versioning.py              # New: VersionEntryData + VersionFileData plain dataclasses (shared type, no Pydantic)
├── loader.py                  # Modified: add version_file: VersionFileData | None to Product dataclass
└── renderer.py                # Modified: render_version_table() + append to document

# New frontend files
src/web-editor/frontend/src/
├── components/
│   └── edit/
│       └── VersioningPanel.vue  # New: version selector + version_name field + CRUD table
└── stores/
    └── versioning.js            # New: Pinia store for versioning data

# Modified frontend files
src/web-editor/frontend/src/
├── components/
│   ├── TreePanel.vue            # Modified: add "Versions" leaf node per product
│   ├── MainPanel.vue            # Modified: add VersioningPanel case for type='versions'
│   ├── CommitPanel.vue          # Modified: add per-product version note prompt step
│   └── edit/
│       └── ProductEdit.vue      # Modified: add "Release" button + release popup

# Documentation
docs/
└── product-versioning/
    ├── overview.md              # New: feature description and release workflow
    └── file-structure.md        # New: versioning/ directory layout and JSON schemas
```

**Structure Decision**: Version logic is isolated in a new `routers/versioning.py` router and `models/versioning.py` module, following the existing pattern of one router file per domain (products, git, units, etc.). A new `src/versioning.py` module defines plain Python dataclasses (`VersionEntryData`, `VersionFileData`) as the shared type used by `src/loader.py` and `src/renderer.py` — keeping the CLI build pipeline free of any Pydantic dependency. The web editor's `models/versioning.py` Pydantic models map to/from these shared dataclasses at the router boundary. Frontend follows the existing panel-per-node-type pattern: a new `VersioningPanel.vue` is wired in `MainPanel.vue` and a new tree node type `'versions'` is added to `TreePanel.vue`.

## Implementation Notes

### Release Endpoint Flow

`POST /api/products/{shortname}/release` with body `{ "new_version_name": "<name>" }`:

1. Read `infra/<shortname>/versioning/wip.json` — error if missing, malformed, or empty (FR-016, FR-017, FR-018).
2. Derive `version_name` from `wip.json.version_name` — validate `^[A-Za-z0-9._-]+$` (FR-019).
3. Check `infra/<shortname>/versioning/<version_name>.json` does not exist — error if it does (FR-016).
4. Validate `new_version_name` against `^[A-Za-z0-9._-]+$` (FR-019).
5. Write `infra/<shortname>/versioning/<version_name>.json` (copy of current `wip.json`).
6. Regenerate `output/<shortname>.adoc` via `render_product_document()` (which now reads the released version file and adds the version table section).
7. Attempt PDF build via `stages.build_pdf`; log a warning on failure but do not abort.
8. Create `infra/<shortname>/versioning/wip.json` with `version_name = new_version_name` and one seeded entry: `author` and `date` from the last entry of the just-released version; `notes` = "copied from previous version" (FR-010).
9. `write_all()` + `git add -A` + `git commit` with message `release(<shortname>): <version_name>`.
10. `git tag <shortname>-<version_name>` (FR-008).
11. Return `{ version_name, tag, pdf_generated, commit_sha }`.

### Renderer Extension

`src/renderer.py` gains `render_version_table(version_file)` which produces an AsciiDoc table with columns: Version, Date, Author(s), Notes. `render_product_document()` is extended to append this section (headed `== Version History`) after the global suffix include, when the product has a resolved version file.

`src/loader.py` is extended to detect and load `infra/<shortname>/versioning/wip.json` (for in-progress builds) or the most recent released version (for release builds). The `Product` dataclass gains an optional `version_file: Optional[VersionFile]` field.

### Commit-Time Version Note

`POST /api/git/commit` body gains an optional field:
```json
"version_notes": [
  { "product_shortname": "acme-crm", "author": "Firstname, Lastname", "date": "2026-05-26", "notes": "..." }
]
```
Before `write_all()`, the backend appends each note as a new `VersionEntry` to the corresponding product's `wip.json`. The frontend `CommitPanel.vue` shows a collapsible per-product section for each product with pending changes, allowing the user to optionally fill in a version note or leave it empty.

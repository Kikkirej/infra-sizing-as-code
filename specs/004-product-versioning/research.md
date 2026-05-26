# Research: Product Version Management

## Version File Storage Location

**Decision**: Store version files in `infra/<product_shortname>/versioning/` — a new subdirectory within each product's existing `infra/` directory.

**Rationale**: Constitution principle I requires all state in Git. Placing version files inside the product's existing `infra/<shortname>/` directory keeps them co-located with the product data they describe and ensures they are committed, diffed, and tagged alongside the sizing data. The `versioning/` subdirectory isolates versioning files from sizing JSON files without adding a top-level directory.

**Alternatives considered**:
- Top-level `versioning/<shortname>/` directory: separates version data from product data, making cross-file diffs harder to read.
- Inline in `meta.json`: mixes identity/display metadata with changelog history; breaks existing loaders.

---

## Release Endpoint vs CLI-Only

**Decision**: Implement the release as a backend REST endpoint (`POST /api/products/{shortname}/release`) called from the web editor. The CLI build pipeline is not involved in the release action itself.

**Rationale**: Spec User Story 3 describes the release as a UI-driven action that shows a popup for the new WIP version name. The web editor is the primary interface for this project; a REST endpoint integrates cleanly into the existing FastAPI router pattern. The CLI build pipeline (`build.py`) is for generating output artifacts from committed state — it is not the right layer for interactive user flows.

**Alternatives considered**:
- Git hook triggered on commit: cannot show a popup; would block non-release commits unnecessarily.
- CLI command invoked from the frontend via subprocess: bypasses the REST API layer; fragile in Docker.

---

## PDF Generation at Release Time

**Decision**: The release endpoint attempts PDF generation synchronously via `src.stages.build_pdf` (which calls asciidoctor). If asciidoctor is unavailable or the build fails, a warning is logged and the release proceeds without a PDF. The `pdf_generated: bool` flag in the response indicates the outcome.

**Rationale**: PDF generation requires asciidoctor, which is installed in the Docker environment but may not be present in all local dev setups. Making it best-effort keeps the release endpoint robust: the core release actions (version file, git tag, new wip.json) always happen; the PDF is a bonus artifact. The frontend can surface a warning to the user when `pdf_generated: false`.

**Alternatives considered**:
- Require PDF generation and fail release if asciidoctor is missing: breaks local dev setups unnecessarily.
- Defer PDF generation to a background job: over-engineered for the local/internal scope; adds async complexity.

---

## Version History in the Renderer

**Decision**: Extend `src/loader.py` to load `versioning/wip.json` (or a specified released version file) into a new optional `version_file` field on the `Product` dataclass. Extend `src/renderer.py` with a `render_version_table()` function that generates an AsciiDoc table and is called from `render_product_document()` to append a `== Version History` section when `product.version_file` is present.

**Rationale**: Placing version rendering in `src/renderer.py` and loading in `src/loader.py` means both the CLI build pipeline and the release endpoint use the same rendering path — one place to change formatting. The CLI build will automatically include version history in all future `build.py` runs, not just at release time.

**Alternatives considered**:
- Render version table only at release time in the release endpoint: duplicates rendering logic; CLI builds would lack version history.
- Store a pre-rendered AsciiDoc fragment: breaks the "files are the source of truth" principle; adds generated artifacts.

---

## Author Validation Regex

**Decision**: Single-author regex: `^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*, [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ' -]*$`. Multi-author: split on `;\s*`, validate each token with the single-author regex. Validation runs on both frontend (Vue reactive input) and backend (Pydantic `field_validator`).

**Rationale**: The pattern `Firstname, Lastname` (with comma and one space) is the canonical format. Supporting `À-ÿ` covers common accented European characters. Supporting hyphens and apostrophes in names (`Anne-Marie`, `O'Brien`) avoids rejecting valid names. The explicit comma+space separator makes the boundary unambiguous when splitting multi-author strings on semicolons.

**Alternatives considered**:
- Strict ASCII-only (`[A-Za-z]+`): rejects valid names with accents, hyphens, or apostrophes.
- Free-text with no validation: violates FR-004 and SC-004; allows invalid entries to persist.

---

## Commit-Time Version Note Integration

**Decision**: Extend `POST /api/git/commit` to accept an optional `version_notes` array. Each element specifies a `product_shortname`, `author`, `date`, and `notes`. The backend validates each note, appends entries to the corresponding `wip.json` files, then proceeds with `write_all()` and the git commit as normal. Notes for products not in the current change set are also accepted (a user may add a note to any product on any commit).

**Rationale**: Keeping version note appending inside the existing commit endpoint avoids a separate round-trip and keeps the atomic guarantee: if the commit fails, no wip.json changes are persisted. The frontend `CommitPanel.vue` shows the prompt between the change list and the commit button — the user fills in notes (or skips) before clicking commit.

**Alternatives considered**:
- Separate `POST /products/{shortname}/versioning/entries` call before commit: two-step flow; if commit fails after note write, the note is orphaned in `wip.json`.
- Git pre-commit hook: cannot surface a UI prompt from a CLI hook; spec specifies web editor only.

---

## `version_name` Character Restrictions

**Decision**: Validate `version_name` against `^[A-Za-z0-9._-]+$` on both frontend and backend. This set is safe for all major filesystems and satisfies git tag naming rules without escaping.

**Rationale**: The `version_name` is used as both a filename (`versioning/<version_name>.json`) and part of a git tag (`<shortname>-<version_name>`). Characters outside `[A-Za-z0-9._-]` can cause silent failures on case-insensitive filesystems, Windows paths, or git tag parsing. Common version strings (`1.0.0`, `v2-beta`, `release_1`) all fit within this set.

---

## Version Selector — Read vs. Write Mode

**Decision**: The Versions panel fetches the list of available version filenames from `GET /api/products/{shortname}/versioning`. The version selector shows all available versions; WIP is selected by default. Selecting a released version switches the entire panel to read-only mode. Only the WIP version exposes CRUD controls and the `version_name` edit field.

**Rationale**: Immutability of released versions (FR-013) must be enforced in both the UI and the backend. Fetching the version list from the backend ensures the selector reflects actual files on disk, not stale frontend state.

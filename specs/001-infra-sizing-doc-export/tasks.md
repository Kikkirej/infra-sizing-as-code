# Tasks: Infrastructure Sizing Document Export

**Input**: Design documents from `specs/001-infra-sizing-doc-export/`

**Prerequisites**: plan.md ✅ · spec.md ✅ · research.md ✅ · data-model.md ✅ · contracts/ ✅

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no unresolved dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every task description

## Path Conventions

- **Application logic**: `src/` (loader, renderer, stages)
- **Infrastructure definitions**: `infra/` (JSON + AsciiDoc, user-managed)
- **Documentation**: `docs/infra-sizing-doc-export/`
- **CI/CD**: `.gitlab-ci.yml` and `.github/workflows/build.yml` — both required (constitution IV)
- **Generated outputs**: `output/` (gitignored)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the project skeleton. All tasks independent; no user story
can begin until the skeleton exists.

- [X] T001 Create directory structure: `src/`, `src/stages/`, `tests/`, `tests/fixtures/`, `tests/unit/`, `tests/integration/`, `docs/infra-sizing-doc-export/`, `output/`
- [X] T002 [P] Create `src/__init__.py` and `src/stages/__init__.py` (empty package markers)
- [X] T003 [P] Create `.gitignore` — exclude `output/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`
- [X] T004 [P] Create `Dockerfile` at repo root — extend `asciidoctor/docker-asciidoctor:latest`; add Python 3.11 via `apk add --no-cache python3`; add mermaid-cli via `npm install -g @mermaid-js/mermaid-cli`
- [X] T005 [P] Create `pytest.ini` at repo root — register `integration` marker: `markers = integration: requires asciidoctor toolchain (run in CI/Docker only)`

**Checkpoint**: Repo skeleton ready. All source directories exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Define Python dataclasses in `src/loader.py` — `TypedValue` (fields: `type: str`, `unit: str`, `value: float = 0.0`, `formula: str = ""`; `render()` method: static → `"{int(value) if whole else value} {unit}"`, dynamic → `"{formula} {unit}"`), `Partition` (fields: `size: TypedValue`, `performance: str`, `comment: str = ""`), `Server` (fields: `system`, `cpu: TypedValue`, `cpu_clocking`, `memory: TypedValue`, `disk: list[Partition]`, `count: int = 1`, `network: list[str]`, `software: list[str]`, `comment: str`), `FlavourImage`, `Flavour` (no `suppress_count_column` property — count handled inline in renderer), `Size`, `Product` — see data-model.md Python Internal Types section
- [X] T007 Implement fatal precondition checks in `src/loader.py` — `check_theme(repo_root)` raises `SystemExit` if `theme.yml` absent (FR-015); `check_products_json(repo_root)` raises `SystemExit` if `infra/products.json` absent or not valid JSON (FR-022)
- [X] T008 Create `build.py` at repo root — thin entry point: calls `src.build_runner.run(repo_root=Path(__file__).parent)` and exits with its return code; stub `src/build_runner.py` with `run()` returning 0 (FR-008)
- [X] T009 [P] Create `tests/fixtures/minimal-infra/` — minimum valid infra/ tree: one product (`product-a`), one size (`size-s`), one flavour (`flavour-f`), one server with two disk partitions using TypedValue format: `"cpu": {"type": "static", "value": 4, "unit": "vCPU"}`, `"memory": {"type": "static", "value": 16, "unit": "GB"}`, partition sizes as `{"type": "static", "value": 100, "unit": "GB"}`; include all required JSON files and placeholder `.adoc` files
- [X] T010 [P] Create `theme.yml` at repo root — minimal asciidoctor-pdf theme: `extends: default`; `base.font_family: Helvetica`
- [X] T043 Remove `suppress_count_column` property from `Flavour` dataclass in `src/loader.py` — the property `all(s.count == 1 for s in self.servers)` is no longer used; the renderer now handles count inline in the System cell

**Checkpoint**: Foundation ready — fatal checks implemented, entry point wired, fixtures exist with TypedValue format. User story implementation can begin.

---

## Phase 3: User Story 1 — Define Infrastructure and Generate PDF (Priority: P1) 🎯 MVP

**Goal**: Load a full product definition from `infra/` and produce a correct PDF
containing all infrastructure data in the 5-column table format.

**Independent Test**: Run `python build.py` from repo root against `tests/fixtures/minimal-infra/`,
verify `output/product-a.adoc` and `output/product-a.pdf` are produced; confirm the
server table has 5 columns (System | CPU | Memory | Disk | Comment), count shown
inline as `[N]` in System when > 1, and Comment cell contains software + network
bullet list followed by original comment text.

### Loading — `src/loader.py`

- [X] T011 [P] [US1] Implement registry loaders: `load_product_registry(repo_root)` → validates products.json array, checks each product folder exists (FR-016, FR-023); `load_size_registry(product_dir)` → validates sizes.json, checks size folders (FR-019); `load_flavour_registry(size_dir)` → validates flavours.json, checks flavour folders (FR-020)
- [X] T012 [P] [US1] Implement metadata loaders: `load_product_meta(product_dir)` → validates meta.json preamble/suffix path existence (FR-013, FR-015a); `load_size_meta(size_dir)` → loads prefix_text/suffix_text, treats absent/null as `""` (FR-013); `load_flavour_meta(flavour_dir)` → loads optional image entry, validates type is `file`|`mermaid` and value path exists (FR-018)
- [X] T013 [US1] Implement `load_servers(flavour_dir)` in `src/loader.py` — parses `servers.json`; deserialises `cpu` and `memory` fields as `TypedValue` objects (validate `type` is `"static"|"dynamic"`; require `value > 0` when static; require non-empty `formula` when dynamic; `unit` always required); deserialises each `disk[].size` as `TypedValue` with same rules; applies field defaults (`count=1`, `network=[]`, `software=[]`, `comment=""`); validates each server has ≥1 disk partition (FR-024); validates required string fields non-empty (FR-006, FR-007)
- [X] T014 [US1] Implement `load_product(repo_root, shortname, display_name)` in `src/loader.py` — orchestrates T011–T013 for one product; returns `Product` dataclass or appends to error list and returns `None`; covers: missing folder (FR-023), no sizes (FR-003), no flavours (FR-003), no servers (FR-003), missing preamble/suffix (FR-015a)

### Rendering — `src/renderer.py`

- [X] T015 [US1] Implement `render_document_header(product)` in `src/renderer.py` — returns AsciiDoc document header string: `= {display_name}`, `:doctype: book`, `:toc:`, `:title-page:`, `:revdate: {date}`, `:nofooter:`
- [X] T016 [P] [US1] Re-implement `render_server_table(flavour)` in `src/renderer.py` — always 5 columns `[cols="15,14,13,43,33",options="header"]`; column headers: `System | CPU | Memory | Disk | Comment`; System cell: `{server.system}` when `count == 1`, `{server.system} [{server.count}]` when `count > 1`; CPU cell: `{server.cpu.render()} ({server.cpu_clocking})`; Memory cell: `{server.memory.render()}`; Disk cell: `a|` with nested `!===` table (`[cols="3,3,3"]` with headers `! Size ! Perform- +\nance ! Comment/ +\nUsage`, one row per partition using `partition.size.render()`, blank comment cell when absent); Comment cell: `a|` containing software items as `* {item}` bullets, then network items as `* {item}` bullets, then original comment text (if any) appended after bullets; blank cell when all three are absent/empty — remove all count-suppression logic and separate Network/Software columns (FR-006, FR-006a, FR-007, FR-007a)
- [X] T017 [US1] Implement `render_flavour_section(flavour, product_shortname, size_shortname)` in `src/renderer.py` — heading (`=== {display_name}`); optional image: `image::infra/…[]` for `type:file`; mermaid block with embedded `.mmd` content for `type:mermaid`; optional `include::infra/…/preamble.adoc[]`; server table from T016; optional `include::infra/…/suffix.adoc[]` (FR-017, FR-018)
- [X] T018 [US1] Implement `render_size_section(size, product_shortname, is_single_size)` in `src/renderer.py` — conditional `== {display_name}` heading (suppress when `is_single_size=True`: FR-004, SC-003); `{prefix_text}`; flavour sections from T017; `{suffix_text}` (FR-005)
- [X] T019 [US1] Implement `render_product_document(product, build_date)` in `src/renderer.py` — assembles full document: header + `include::infra/preamble.adoc[]` + `include::infra/{shortname}/preamble.adoc[]` + size sections (pass `is_single_size=len(sizes)==1`) + `include::infra/{shortname}/suffix.adoc[]` + `include::infra/suffix.adoc[]`; all paths relative to repo root (resolved via `-B` flag) (FR-009, FR-010, FR-011, FR-013a)

### Stage 1 — `src/stages/generate.py`

- [X] T020 [US1] Implement `generate(repo_root, products, errors)` in `src/stages/generate.py` — creates `output/` dir if absent; for each Product: calls `render_product_document()`, writes to `output/{shortname}.adoc`; on exception appends to errors list; returns list of successfully written `.adoc` paths (FR-008)

### Stage 2 — `src/stages/build_pdf.py`

- [X] T021 [US1] Implement `build_pdf(repo_root, adoc_paths, errors)` in `src/stages/build_pdf.py` — for each `.adoc` path: invokes `asciidoctor-pdf -r asciidoctor-diagram -a pdf-theme=theme.yml -a pdf-themesdir={repo_root} -B {repo_root} -D output/ {adoc}` via `subprocess.run(capture_output=True, text=True)`; non-zero return code → append stderr to errors; returns list of successfully produced `.pdf` paths (FR-008)

### Unit Tests

- [X] T022 [P] [US1] Write `tests/unit/test_loader.py` — test: valid servers.json with TypedValue cpu/memory/disk.size loads into correct dataclasses; static TypedValue with `value: 8, unit: "vCPU"` → `render()` returns `"8 vCPU"`; dynamic TypedValue with `formula: "n × 4", unit: "vCPU"` → `render()` returns `"n × 4 vCPU"`; integer static value renders without decimal (`8` not `8.0`); empty `disk` raises validation error (FR-024); missing required `unit` in TypedValue raises validation error; `count` defaults to 1; absent `network`/`software` default to `[]`
- [X] T023 [P] [US1] Rewrite `tests/unit/test_renderer.py` for new 5-column layout — test: `render_server_table()` always produces 5 columns (`[cols="15,14,13,43,33"` in output); server with `count == 1` → System cell is plain `{system}` with no count annotation; server with `count > 1` → System cell is `{system} [{count}]` (e.g. `Application Server [3]`); CPU cell format is `"{cpu.render()} ({cpu_clocking})"`; Disk cell contains `!===` nested table; Comment cell contains software bullets then network bullets then comment text; server with no software/network/comment → blank `a|` cell; `render_size_section()` suppresses heading when `is_single_size=True` (FR-004); `render_flavour_section()` emits no `include::` line when `has_preamble=False` and no `include::` when `has_suffix=False` (FR-017) — remove all old suppress_count_column / separate-network-software-column tests

### Wire-Up

- [X] T024 [US1] Wire full US1 pipeline in `src/build_runner.py` — `run()` calls: `check_theme()`, `check_products_json()`, `load_product_registry()`, `load_product()` for each entry, `generate()`, `build_pdf()`; prints progress to stdout; prints errors to stderr; returns 1 if errors else 0

**Checkpoint**: Run `python build.py` against `tests/fixtures/minimal-infra/` (with a `theme.yml`). Verify `output/product-a.pdf` is produced; open PDF and confirm server table has 5 columns, count inline in System cell, and software+network+comment in Comment cell.

---

## Phase 4: User Story 2 — Multi-Product Build with Per-Product Documents (Priority: P2)

**Goal**: N products defined in the registry → exactly N PDFs, each with
correct section order; one product failure does not block others.

**Independent Test**: Add a second product to `tests/fixtures/`; run `python build.py`;
verify two PDFs are produced. Then deliberately break one product (remove its
`sizes.json`); verify one PDF is produced, one error is reported, exit code is 1.

- [X] T025 [P] [US2] Add a second product (`product-b`) to `tests/fixtures/minimal-infra/products.json` and create its full directory structure in `tests/fixtures/minimal-infra/product-b/` — distinct sizes and flavours from `product-a`, all servers using TypedValue format
- [X] T026 [US2] Validate `render_product_document()` embeds the correct common preamble/suffix includes and that product-specific preamble/suffix includes differ per product — assert generated `.adoc` content in `tests/unit/test_renderer.py` (FR-010, FR-011)
- [X] T027 [US2] Validate mandated section order in generated `.adoc` for multi-product build: `header → include::infra/preamble.adoc[] → include::infra/{p}/preamble.adoc[] → sizes → include::infra/{p}/suffix.adoc[] → include::infra/suffix.adoc[]` — assert in `tests/unit/test_renderer.py` (FR-009, SC-002)
- [X] T028 [US2] Test per-product error isolation in `tests/unit/test_loader.py` — simulate `load_product()` for two products where one has no sizes; assert errors list has one entry, the valid product still returns a `Product` object (FR-008a)
- [X] T029 [US2] Write integration test `tests/integration/test_build.py` (`@pytest.mark.integration`) — run `build.py` against two-product fixture; assert exactly 2 `.pdf` files in `output/`; assert exit code 0

**Checkpoint**: Two-product build runs end-to-end. Error isolation verified: one broken product fails, other succeeds, exit code 1, successful PDF available.

---

## Phase 5: User Story 3 — Archive Build Artefacts (Priority: P3)

**Goal**: After PDF generation, all successfully produced PDFs are archived into
`output/documents.zip`; partial failures still produce an archive of successful PDFs.

**Independent Test**: Run a full build; verify `output/documents.zip` exists and
contains exactly the successfully generated PDFs. Run with one broken product;
verify ZIP contains only the successful PDF(s) and exit code is 1.

- [X] T030 [US3] Implement `archive(repo_root, pdf_paths)` in `src/stages/archive.py` — creates `output/documents.zip` using `zipfile.ZipFile`; writes each PDF with its basename as the archive member name; handles empty `pdf_paths` gracefully (produces empty archive or skips); returns path to created ZIP (FR-008, SC-005)
- [X] T031 [P] [US3] Write `tests/unit/test_archive.py` — test: ZIP produced for two PDFs contains both members; ZIP produced for empty list is empty or absent; archive member names are basenames only
- [X] T032 [US3] Wire Stage 3 into `src/build_runner.py` — after `build_pdf()`, call `archive(repo_root, successful_pdfs)`; include archive path in final stdout summary; exit code remains 1 if any product failed even if archive succeeded (US3 AS2)
- [X] T033 [US3] Add integration test for full three-stage build to `tests/integration/test_build.py` (`@pytest.mark.integration`) — run `build.py`; assert `output/documents.zip` exists; open ZIP and assert correct PDF member count; assert exit code 0 on clean run
- [X] T034 [US3] Test partial-failure archive: integration test with one broken product — assert ZIP exists and contains only the successful PDF, assert exit code 1 (US3 AS2, FR-008a)

**Checkpoint**: Full three-stage pipeline runs end-to-end. `output/documents.zip` produced after every run containing all successful PDFs.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, CI/CD pipelines, sample infra, and final validation.

- [X] T035 [P] Create `docs/infra-sizing-doc-export/file-structure.md` — document the complete `infra/` directory layout, file naming conventions, registry file schema, TypedValue JSON format, and build output structure (constitution V)
- [X] T036 [P] Create `README.md` at repo root — include: `docker build` command, `docker run` command (FR-021), quickstart steps, link to `docs/infra-sizing-doc-export/file-structure.md`
- [X] T037 [P] Create `.gitlab-ci.yml` at repo root — `build-docs` job using the Docker image; `script: python3 build.py`; `artifacts: paths: [output/*.pdf, output/documents.zip]` with `when: always` (constitution IV; see `contracts/build-contract.md`)
- [X] T038 [P] Create `.github/workflows/build.yml` — equivalent GitHub Actions pipeline: checkout, docker build, docker run, upload-artifact with `if: always()` (constitution IV; see `contracts/build-contract.md`)
- [X] T039 [P] Create sample `infra/` structure at repo root — `products.json` with two products (`acme-crm`, `acme-erp`), `preamble.adoc`, `suffix.adoc`, and complete product directories for both (multiple sizes and flavours per product); all `servers.json` files use TypedValue format for `cpu`, `memory`, and `disk[].size` — serves as the working example from `quickstart.md`
- [X] T040 Re-run quickstart validation after new rendering — (a) execute `docker build` + `docker run` against the 2-product sample `infra/` from T039 (after T016 + T043 complete); verify 2 PDFs and ZIP produced; open PDFs and confirm 5-column table (System | CPU | Memory | Disk | Comment), count shown as `[N]` in System cell when > 1, and software+network+comment merged in Comment cell (SC-004); (b) run against a 5-product × 3-size fixture and confirm build completes within 5 minutes (SC-001); fix any discrepancies
- [X] T041 [P] Review and finalise `.gitignore` — confirm `output/`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/` all excluded
- [X] T042 Final code review pass — verify: all `src/` modules have correct docstring-free, well-named functions; `build.py` delegates to `src/build_runner.py`; no dead code; stdlib-only imports throughout; TypedValue used consistently for cpu/memory/partition.size with no free-text string fallback

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 completion — **MVP**
- **US2 (Phase 4)**: Depends on Phase 3 completion (multi-product extends single-product pipeline)
- **US3 (Phase 5)**: Depends on Phase 3 completion (archive requires PDFs from Stage 2)
  - US2 and US3 can proceed in parallel after Phase 3 completes
- **Polish (Final Phase)**: Depends on Phases 3, 4, 5 all complete

### Open Task Dependencies

- T043 first (remove `suppress_count_column` before T016 since T016 must not use it)
- T016 [P] after T043 (new render_server_table implementation)
- T023 [P] after T016 (tests must match new column layout)
- T040 after T016 + T023 (re-validation needs correct renderer)

T016 and T023 can be written in parallel (both after T043).

---

## Parallel Examples

### Current Open Tasks
```
Sequential: T043 (remove suppress_count_column) → then parallel:
  T016 (re-implement render_server_table — 5 columns, count inline, comment merged)
  T023 (rewrite renderer tests for new layout)
Then: T040 (re-run docker validation)
```

---

## Implementation Strategy

### Remaining Work (open tasks: T043, T016, T023, T040)

1. T043 — remove `suppress_count_column` from `Flavour` in `src/loader.py`
2. T016 — re-implement `render_server_table()`: 5 cols, `{system} [{count}]` when count > 1, Comment cell = software + network + original comment
3. T023 — rewrite renderer unit tests to cover new 5-column rendering
4. T040 — re-run docker build + run to validate new rendered output

### MVP: Minimal Change Path

1. T043: 3-line change in `src/loader.py` (remove property)
2. T016: rewrite `render_server_table()` in `src/renderer.py`
3. T023: rewrite `tests/unit/test_renderer.py`
4. T040: docker validate

### Notes

- No external Python packages — stdlib only (`json`, `pathlib`, `subprocess`, `zipfile`, `sys`, `datetime`)
- Unit tests (no toolchain) run locally; integration tests (`@pytest.mark.integration`) run in Docker/CI only
- The JSON data model is unchanged — `network`, `software`, `comment` remain separate fields in `servers.json`; only the renderer changes
- All `include::` paths in generated `.adoc` are relative to repo root; asciidoctor-pdf resolves them via `-B {repo_root}`
- TypedValue used for `cpu`, `memory`, `Partition.size` only — `cpu_clocking`, `performance`, `network`, `software` remain free-text strings

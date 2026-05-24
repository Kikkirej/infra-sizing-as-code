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

- [ ] T001 Create directory structure: `src/`, `src/stages/`, `tests/`, `tests/fixtures/`, `tests/unit/`, `tests/integration/`, `docs/infra-sizing-doc-export/`, `output/`
- [ ] T002 [P] Create `src/__init__.py` and `src/stages/__init__.py` (empty package markers)
- [ ] T003 [P] Create `.gitignore` — exclude `output/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`
- [ ] T004 [P] Create `Dockerfile` at repo root — extend `asciidoctor/docker-asciidoctor:latest`; add Python 3.11 via `apk add --no-cache python3`; add mermaid-cli via `npm install -g @mermaid-js/mermaid-cli`
- [ ] T005 [P] Create `pytest.ini` at repo root — register `integration` marker: `markers = integration: requires asciidoctor toolchain (run in CI/Docker only)`

**Checkpoint**: Repo skeleton ready. All source directories exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T006 Define Python dataclasses in `src/loader.py` — `Partition`, `Server`, `FlavourImage`, `Flavour`, `Size`, `Product` (see data-model.md Python Internal Types section)
- [ ] T007 Implement fatal precondition checks in `src/loader.py` — `check_theme(repo_root)` raises `SystemExit` if `theme.yml` absent (FR-015); `check_products_json(repo_root)` raises `SystemExit` if `infra/products.json` absent or not valid JSON (FR-022)
- [ ] T008 Create `build.py` at repo root — thin entry point: calls `src.build_runner.run(repo_root=Path(__file__).parent)` and exits with its return code; stub `src/build_runner.py` with `run()` returning 0 (FR-008)
- [ ] T009 [P] Create `tests/fixtures/minimal-infra/` — minimum valid infra/ tree: one product (`product-a`), one size (`size-s`), one flavour (`flavour-f`), one server with two disk partitions; include all required JSON files and placeholder `.adoc` files
- [ ] T010 [P] Create `theme.yml` at repo root — minimal asciidoctor-pdf theme: `extends: default`; `base.font_family: Helvetica`

**Checkpoint**: Foundation ready — fatal checks implemented, entry point wired, fixtures exist. User story implementation can begin.

---

## Phase 3: User Story 1 — Define Infrastructure and Generate PDF (Priority: P1) 🎯 MVP

**Goal**: Load a full product definition from `infra/` and produce a correct PDF
containing all infrastructure data in the mandated table format.

**Independent Test**: Create `tests/fixtures/minimal-infra/` structure (done in T009),
run `python build.py` from repo root, verify `output/product-a.adoc` and
`output/product-a.pdf` are produced; open PDF and confirm 9-column server table
with both disk partitions is present.

### Loading — `src/loader.py`

- [ ] T011 [P] [US1] Implement registry loaders: `load_product_registry(repo_root)` → validates products.json array, checks each product folder exists (FR-016, FR-023); `load_size_registry(product_dir)` → validates sizes.json, checks size folders (FR-019); `load_flavour_registry(size_dir)` → validates flavours.json, checks flavour folders (FR-020)
- [ ] T012 [P] [US1] Implement metadata loaders: `load_product_meta(product_dir)` → validates meta.json preamble/suffix path existence (FR-013, FR-015a); `load_size_meta(size_dir)` → loads prefix_text/suffix_text, treats absent/null as `""` (FR-013); `load_flavour_meta(flavour_dir)` → loads optional image entry, validates type is `file`|`mermaid` and value path exists (FR-018)
- [ ] T013 [US1] Implement `load_servers(flavour_dir)` in `src/loader.py` — parses `servers.json`; applies field defaults (`count=1`, `network=[]`, `software=[]`, `comment=""`); validates each server has ≥1 disk partition (FR-024); validates required string fields non-empty (FR-006, FR-007)
- [ ] T014 [US1] Implement `load_product(repo_root, shortname, display_name)` in `src/loader.py` — orchestrates T011–T013 for one product; returns `Product` dataclass or appends to error list and returns `None`; covers: missing folder (FR-023), no sizes (FR-003), no flavours (FR-003), no servers (FR-003), missing preamble/suffix (FR-015a)

### Rendering — `src/renderer.py`

- [ ] T015 [US1] Implement `render_document_header(product)` in `src/renderer.py` — returns AsciiDoc document header string: `= {display_name}`, `:doctype: book`, `:toc:`, `:title-page:`, `:revdate: {date}`, `:nofooter:`
- [ ] T016 [P] [US1] Implement `render_server_table(servers)` in `src/renderer.py` — 9-column AsciiDoc table (`[cols="2,1,1,1,1,3,2,2,2",options="header"]`); use `a|` cells for Disk, Network, Software; render each partition as `* {size}, {performance} — {comment}` (omit ` — {comment}` if absent); render network/software items as `* {item}` each; blank cell when list empty (FR-006, FR-006a, FR-007, FR-007a)
- [ ] T017 [US1] Implement `render_flavour_section(flavour, product_shortname, size_shortname)` in `src/renderer.py` — heading (`=== {display_name}`); optional image: `image::infra/…[]` for `type:file`; mermaid block with embedded `.mmd` content for `type:mermaid`; optional `include::infra/…/preamble.adoc[]`; server table from T016; optional `include::infra/…/suffix.adoc[]` (FR-017, FR-018)
- [ ] T018 [US1] Implement `render_size_section(size, product_shortname, is_single_size)` in `src/renderer.py` — conditional `== {display_name}` heading (suppress when `is_single_size=True`: FR-004); `{prefix_text}`; flavour sections from T017; `{suffix_text}` (FR-005)
- [ ] T019 [US1] Implement `render_product_document(product, build_date)` in `src/renderer.py` — assembles full document: header + `include::infra/preamble.adoc[]` + `include::infra/{shortname}/preamble.adoc[]` + size sections (pass `is_single_size=len(sizes)==1`) + `include::infra/{shortname}/suffix.adoc[]` + `include::infra/suffix.adoc[]`; all paths relative to repo root (resolved via `-B` flag) (FR-009, FR-010, FR-011, FR-013a)

### Stage 1 — `src/stages/generate.py`

- [ ] T020 [US1] Implement `generate(repo_root, products, errors)` in `src/stages/generate.py` — creates `output/` dir if absent; for each Product: calls `render_product_document()`, writes to `output/{shortname}.adoc`; on exception appends to errors list; returns list of successfully written `.adoc` paths (FR-008)

### Stage 2 — `src/stages/build_pdf.py`

- [ ] T021 [US1] Implement `build_pdf(repo_root, adoc_paths, errors)` in `src/stages/build_pdf.py` — for each `.adoc` path: invokes `asciidoctor-pdf -r asciidoctor-diagram -a pdf-theme=theme.yml -a pdf-themesdir={repo_root} -B {repo_root} -D output/ {adoc}` via `subprocess.run(capture_output=True, text=True)`; non-zero return code → append stderr to errors; returns list of successfully produced `.pdf` paths (FR-008)

### Unit Tests

- [ ] T022 [P] [US1] Write `tests/unit/test_loader.py` — test: valid servers.json loads correctly; empty `disk` raises validation error (FR-024); missing `sizes.json` triggers product error; `count` defaults to 1; absent `network`/`software` default to `[]`
- [ ] T023 [P] [US1] Write `tests/unit/test_renderer.py` — test: `render_server_table()` produces correct 9-column table; single partition renders one bullet; multi-partition renders multiple bullets; empty network → blank `a|` cell; `render_size_section()` suppresses heading when `is_single_size=True` (FR-004)

### Wire-Up

- [ ] T024 [US1] Wire full US1 pipeline in `src/build_runner.py` — `run()` calls: `check_theme()`, `check_products_json()`, `load_product_registry()`, `load_product()` for each entry, `generate()`, `build_pdf()`; prints progress to stdout; prints errors to stderr; returns 1 if errors else 0

**Checkpoint**: Run `python build.py` against `tests/fixtures/minimal-infra/` (with a `theme.yml`). Verify `output/product-a.pdf` is produced and contains a 9-column server table with two disk partition bullets.

---

## Phase 4: User Story 2 — Multi-Product Build with Per-Product Documents (Priority: P2)

**Goal**: N products defined in the registry → exactly N PDFs, each with
correct section order; one product failure does not block others.

**Independent Test**: Add a second product to `tests/fixtures/`; run `python build.py`;
verify two PDFs are produced. Then deliberately break one product (remove its
`sizes.json`); verify one PDF is produced, one error is reported, exit code is 1.

- [ ] T025 [P] [US2] Add a second product (`product-b`) to `tests/fixtures/minimal-infra/products.json` and create its full directory structure in `tests/fixtures/minimal-infra/product-b/` — distinct sizes and flavours from `product-a`
- [ ] T026 [US2] Validate `render_product_document()` embeds the correct common preamble/suffix includes and that product-specific preamble/suffix includes differ per product — assert generated `.adoc` content in unit test (FR-010, FR-011)
- [ ] T027 [US2] Validate mandated section order in generated `.adoc` for multi-product build: `header → include::infra/preamble.adoc[] → include::infra/{p}/preamble.adoc[] → sizes → include::infra/{p}/suffix.adoc[] → include::infra/suffix.adoc[]` — assert in `tests/unit/test_renderer.py` (FR-009)
- [ ] T028 [US2] Test per-product error isolation in `tests/unit/test_loader.py` — simulate `load_product()` for two products where one has no sizes; assert errors list has one entry, the valid product still returns a `Product` object (FR-008a)
- [ ] T029 [US2] Write integration test `tests/integration/test_build.py` (`@pytest.mark.integration`) — run `build.py` against two-product fixture; assert exactly 2 `.pdf` files in `output/`; assert exit code 0

**Checkpoint**: Two-product build runs end-to-end. Error isolation verified: one broken product fails, other succeeds, exit code 1, successful PDF available.

---

## Phase 5: User Story 3 — Archive Build Artefacts (Priority: P3)

**Goal**: After PDF generation, all successfully produced PDFs are archived into
`output/documents.zip`; partial failures still produce an archive of successful PDFs.

**Independent Test**: Run a full build; verify `output/documents.zip` exists and
contains exactly the successfully generated PDFs. Run with one broken product;
verify ZIP contains only the successful PDF(s) and exit code is 1.

- [ ] T030 [US3] Implement `archive(repo_root, pdf_paths)` in `src/stages/archive.py` — creates `output/documents.zip` using `zipfile.ZipFile`; writes each PDF with its basename as the archive member name; handles empty `pdf_paths` gracefully (produces empty archive or skips); returns path to created ZIP (FR-008, SC-005)
- [ ] T031 [P] [US3] Write `tests/unit/test_archive.py` — test: ZIP produced for two PDFs contains both members; ZIP produced for empty list is empty or absent; archive member names are basenames only
- [ ] T032 [US3] Wire Stage 3 into `src/build_runner.py` — after `build_pdf()`, call `archive(repo_root, successful_pdfs)`; include archive path in final stdout summary; exit code remains 1 if any product failed even if archive succeeded (US3 AS2)
- [ ] T033 [US3] Add integration test for full three-stage build to `tests/integration/test_build.py` (`@pytest.mark.integration`) — run `build.py`; assert `output/documents.zip` exists; open ZIP and assert correct PDF member count; assert exit code 0 on clean run
- [ ] T034 [US3] Test partial-failure archive: integration test with one broken product — assert ZIP exists and contains only the successful PDF, assert exit code 1 (US3 AS2, FR-008a)

**Checkpoint**: Full three-stage pipeline runs end-to-end. `output/documents.zip` produced after every run containing all successful PDFs.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, CI/CD pipelines, sample infra, and final validation.

- [ ] T035 [P] Create `docs/infra-sizing-doc-export/file-structure.md` — document the complete `infra/` directory layout, file naming conventions, registry file schema, and build output structure (constitution V)
- [ ] T036 [P] Create `README.md` at repo root — include: `docker build` command, `docker run` command (FR-021), quickstart steps, link to `docs/infra-sizing-doc-export/file-structure.md`
- [ ] T037 [P] Create `.gitlab-ci.yml` at repo root — `build-docs` job using the Docker image; `script: python3 build.py`; `artifacts: paths: [output/*.pdf, output/documents.zip]` with `when: always` (constitution IV; see `contracts/build-contract.md`)
- [ ] T038 [P] Create `.github/workflows/build.yml` — equivalent GitHub Actions pipeline: checkout, docker build, docker run, upload-artifact with `if: always()` (constitution IV; see `contracts/build-contract.md`)
- [ ] T039 [P] Create sample `infra/` structure at repo root — `products.json`, `preamble.adoc`, `suffix.adoc`, and one complete product directory — gives users a working starting point
- [ ] T040 Run `quickstart.md` validation — execute `docker build` + `docker run` against the sample `infra/` from T039; verify PDF and ZIP produced; fix any discrepancies
- [ ] T041 [P] Review and finalise `.gitignore` — confirm `output/`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/` all excluded
- [ ] T042 Final code review pass — verify: all `src/` modules have correct docstring-free, well-named functions; `build.py` delegates to `src/build_runner.py`; no dead code; stdlib-only imports throughout

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

### Within Phase 3 (US1)

- T011 [P] and T012 [P]: parallel — independent loaders, different functions
- T013: after T011 (uses registry loading pattern)
- T014: after T011, T012, T013 — orchestrates all loaders
- T015, T016 [P]: parallel — independent rendering functions
- T017: after T016 (uses server table renderer)
- T018: after T017 (uses flavour section renderer)
- T019: after T018 (uses size section renderer)
- T020: after T019 (uses product document renderer)
- T021: after T020 (processes `.adoc` output)
- T022 [P], T023 [P]: parallel — can be written alongside implementation
- T024: after T014, T021 (wires all loaders and stages)

---

## Parallel Examples

### Phase 3 (US1) — Loading Layer
```
Parallel: T011 (registry loaders) + T012 (metadata loaders)
Then sequential: T013 (server loader) → T014 (load_product orchestrator)
```

### Phase 3 (US1) — Rendering Layer
```
Parallel: T015 (header) + T016 (server table)
Then sequential: T017 (flavour) → T018 (size) → T019 (product document)
```

### Phase 3 (US1) — Tests
```
Parallel alongside implementation: T022 (loader tests) + T023 (renderer tests)
```

### Phase 4 + Phase 5 after Phase 3 completes
```
Parallel: Phase 4 (US2 multi-product) + Phase 5 (US3 archive)
```

### Final Phase
```
Parallel: T035 (docs) + T036 (README) + T037 (GitLab CI) + T038 (GitHub Actions) + T039 (sample infra) + T041 (gitignore review)
Then: T040 (quickstart validation) → T042 (final review)
```

---

## Implementation Strategy

### MVP: User Story 1 Only (Phases 1–3)

1. Phase 1: Setup → skeleton exists
2. Phase 2: Foundational → fatal checks + entry point + fixtures
3. Phase 3: US1 → full single-product definition-to-PDF pipeline
4. **STOP AND VALIDATE**: Run against `tests/fixtures/minimal-infra/`; open PDF; confirm 9-column table, partition rendering, single-size suppression
5. Ship MVP if ready

### Incremental Delivery

1. Phases 1–3 → single product PDF pipeline (MVP)
2. Phase 4 (US2) → multi-product build, error isolation
3. Phase 5 (US3) → ZIP archive
4. Final Phase → CI/CD, documentation, sample infra

### Parallel Team Strategy

After Phase 2 completes:
- **Developer A**: Phase 3 (US1) — loading + rendering + Stage 1 + Stage 2
- **Developer B**: Phase 5 (US3) — Stage 3 (archive) — depends on Stage 2 interface only
- After Phase 3: Developer B continues US3 integration; Developer A moves to Phase 4 (US2)

---

## Notes

- No external Python packages — stdlib only (`json`, `pathlib`, `subprocess`, `zipfile`, `sys`, `datetime`)
- Unit tests (no toolchain) run locally; integration tests (`@pytest.mark.integration`) run in Docker/CI only
- Commit after each completed phase checkpoint
- The `output/` directory is gitignored; never commit generated `.adoc`, `.pdf`, or `.zip` files
- All `include::` paths in generated `.adoc` are relative to repo root; asciidoctor-pdf resolves them via `-B {repo_root}`
- Every FR tag in task descriptions maps to a specific requirement in `spec.md`

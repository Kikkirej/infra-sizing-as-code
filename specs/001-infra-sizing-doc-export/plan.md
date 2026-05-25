# Implementation Plan: Infrastructure Sizing Document Export

**Branch**: `001-infra-sizing-doc-export` | **Date**: 2026-05-24 | **Spec**: `specs/001-infra-sizing-doc-export/spec.md`

**Input**: Feature specification from `specs/001-infra-sizing-doc-export/spec.md`

## Summary

Build a three-stage Python 3.11 CLI pipeline (`build.py`) that reads declarative
infrastructure definitions from a hierarchical `infra/` directory tree (JSON +
AsciiDoc), generates one AsciiDoc document per product, converts each to PDF via
`asciidoctor-pdf`, and archives all PDFs into a single ZIP. Both GitLab CI and
GitHub Actions pipelines invoke the same `build.py` entry point inside a Docker
container based on `asciidoctor/docker-asciidoctor` extended with Python 3.11
and mermaid-cli.

## Technical Context

**Language/Version**: Python 3.11+ (stdlib only — json, pathlib, subprocess, zipfile, sys, datetime)

**Primary Dependencies**: `asciidoctor-pdf` (subprocess), `asciidoctor-diagram`
(asciidoctor-pdf extension flag `-r asciidoctor-diagram`), `mmdc` mermaid-cli
(invoked indirectly by asciidoctor-diagram). No third-party Python packages.

**Storage**: Filesystem — hierarchical JSON + AsciiDoc under `infra/`; generated
outputs under `output/` (gitignored); final archive `output/documents.zip`.

**Testing**: pytest — unit tests (no toolchain required), integration tests
(require asciidoctor toolchain; CI-gated via `@pytest.mark.integration`).

**Target Platform**: Linux, Docker container (`asciidoctor/docker-asciidoctor`
extended with Python 3.11 + `@mermaid-js/mermaid-cli`). Local builds via
`docker run` (see FR-021 / README.md).

**Project Type**: CLI batch build tool / document generator

**Performance Goals**: Full build for 5 products × 3 sizes completes within
5 minutes (SC-001).

**Constraints**: Python stdlib only; fully offline at build time (no network
access during `mmdc` or asciidoctor-pdf); single `build.py` entry point at
repo root (FR-008); failure isolation per product (FR-008a).

**Scale/Scope**: N products, each with M sizes, K flavours per size, J servers
per flavour — all bounded by filesystem and 5-minute wall-clock constraint.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-evaluated post-design below.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git as Single Source of Truth | ✅ PASS | All infra defs are versioned files; `output/` gitignored; no side-channel state |
| II. File-First Architecture | ✅ PASS | `src/` for Python logic; `infra/` for definitions; `docs/` for documentation |
| III. Infrastructure as Code | ✅ PASS | All infra defined declaratively in `infra/`; no manual provisioning |
| IV. CI/CD Portability | ✅ PASS | GitLab CI + GitHub Actions both required; shared `build.py` entry point |
| V. Documentation-Driven | ✅ PASS | `docs/infra-sizing-doc-export/` + `README.md` (FR-021) required before merge |

**No violations. Complexity Tracking table not required.**

**Post-design re-evaluation**: All principles remain satisfied after Phase 1 design.
The `build.py` root entry point is a thin delegator; all logic lives in `src/`.
`include::` paths in generated AsciiDoc use asciidoctor-pdf's `-B` base-directory
flag so they are resolved relative to repo root, not the `output/` directory.

## Project Structure

### Documentation (this feature)

```text
specs/001-infra-sizing-doc-export/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── json-schemas.md  # Phase 1 output — JSON file format specs
│   └── build-contract.md  # Phase 1 output — CLI and output contract
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
# Entry point (repo root — per FR-008)
build.py               # Thin CLI entry point; delegates to src/

# Build environment (for FR-021 docker run)
Dockerfile             # Extends asciidoctor/docker-asciidoctor; adds Python 3.11 + mermaid-cli

# PDF theme (required — FR-015)
theme.yml

# Documentation (FR-021)
README.md

# Application logic (per constitution — File-First Architecture)
src/
├── __init__.py
├── loader.py            # JSON loading and validation (FR-016, FR-022, FR-023, FR-024)
├── build_runner.py      # Build orchestrator: wires three stages, accumulates errors, returns exit code
├── renderer.py          # AsciiDoc string generation (tables, include blocks, cover attrs)
└── stages/
    ├── __init__.py
    ├── generate.py      # Stage 1: JSON → .adoc per product
    ├── build_pdf.py     # Stage 2: asciidoctor-pdf subprocess per product
    └── archive.py       # Stage 3: zipfile archive of all successful PDFs

# Tests
tests/
├── fixtures/
│   └── minimal-infra/   # Minimal valid infra/ tree for unit + integration tests
│       ├── products.json
│       ├── preamble.adoc
│       ├── suffix.adoc
│       └── product-a/
│           ├── meta.json
│           ├── sizes.json
│           ├── preamble.adoc
│           ├── suffix.adoc
│           └── size-s/
│               ├── meta.json
│               ├── flavours.json
│               └── flavour-f/
│                   ├── meta.json
│                   └── servers.json
├── unit/
│   ├── test_loader.py
│   └── test_renderer.py
└── integration/
    └── test_build.py    # Requires asciidoctor toolchain; @pytest.mark.integration

# Infrastructure definitions (per constitution — IaC)
infra/
├── products.json
├── preamble.adoc
├── suffix.adoc
└── {product-shortname}/
    ├── meta.json
    ├── sizes.json
    ├── preamble.adoc
    ├── suffix.adoc
    └── {size-shortname}/
        ├── meta.json
        ├── flavours.json
        └── {flavour-shortname}/
            ├── meta.json
            ├── preamble.adoc    # optional
            ├── suffix.adoc      # optional
            └── servers.json

# Generated outputs (gitignored)
output/
├── {product-shortname}.adoc
├── {product-shortname}.pdf
└── documents.zip

# Documentation (per constitution — Documentation-Driven)
docs/
└── infra-sizing-doc-export/
    └── file-structure.md

# CI/CD pipelines (both required — per constitution IV)
.gitlab-ci.yml
.github/
└── workflows/
    └── build.yml
```

**Structure Decision**: `build.py` at repo root is the thin entry point mandated
by FR-008, importing and delegating to `src/`. All application logic is in `src/`
per constitution principle II. The `infra/` tree is user-managed data; the `output/`
directory is gitignored build artifact space. Both CI/CD platforms invoke
`python build.py` inside the same Docker container.

## Complexity Tracking

*No violations to justify — all constitution gates pass.*

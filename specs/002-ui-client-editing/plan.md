# Implementation Plan: Infrastructure Sizing Web Editor

**Branch**: `002-ui-client-editing` | **Date**: 2026-05-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-ui-client-editing/spec.md`

---

## Summary

Build a local web-based editor for the infra sizing repository. Operators launch it with
`docker compose up -d` from the repo root and interact with a Vue.js 3 SPA (served by
Vite dev server with hot reload) backed by a FastAPI REST API. All edits are held in a
module-level in-memory state on the backend until the operator explicitly commits; the
commit action writes all modified JSON and `.adoc` files atomically to disk, then creates
a git commit and pushes via SSH agent forwarding. The frontend mirrors state in Pinia
stores and syncs with the backend via REST.

---

## Technical Context

**Language/Version**: Python 3.11+ (backend) · Node.js 20 LTS (frontend)

**Primary Dependencies**:
- Backend: FastAPI 0.111+, Pydantic v2, GitPython 3.x, uvicorn
- Frontend: Vue.js 3.4+, Vite 5.x, Pinia 2.x, Asciidoctor.js 3.x (`asciidoctor` npm)

**Storage**: On-disk JSON files and `.adoc` files in `infra/`; `infra/units.json` (new);
git history is the audit log (Principle I)

**Testing**: pytest + httpx (backend integration tests) · Vitest + Vue Test Utils (frontend)

**Target Platform**: Docker container (Linux/amd64); accessed from host desktop browser
(Chrome, Firefox, Safari desktop — mobile out of scope)

**Project Type**: Web application — local operator tool, single user, no auth

**Performance Goals**:
- Full tree visible within 3 s of editor load (SC-002)
- Commit + push completes within 5 s for ≤ 20 modified files (SC-004)
- Overview panel counts load within 2 s (SC-007)

**Constraints**:
- Launched with a single `docker compose up -d` from repo root (FR-001)
- No user authentication (local tool)
- SSH_AUTH_SOCK forwarded into container for git push (FR-028)
- Desktop browser only; mobile out of scope

**Scale/Scope**: Single operator; infra/ tree bounded by repository (typically < 200 files)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Git as Single Source of Truth | ✅ Pass | All sizing data persisted in git. In-memory state is explicitly ephemeral by design (documented assumption). |
| II. File-First Architecture | ✅ Pass | App code in `src/web-editor/`; sizing data in `infra/`; docs in `docs/web-editor/`. |
| III. Infrastructure as Code | ⚠️ Justified Deviation | `docker-compose.yml` placed at repo root, not `infra/`, to satisfy FR-001 (`docker compose up -d` from root). See Complexity Tracking. |
| IV. CI/CD Portability | ✅ Pass | Both `.gitlab-ci.yml` and `.github/workflows/` must gain a `web-editor` stage (lint + test). |
| V. Documentation-Driven Development | ✅ Pass | `docs/web-editor/overview.md` and `docs/web-editor/runbook.md` required before merge. |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-ui-client-editing/
├── plan.md           # This file
├── research.md       # Phase 0 output
├── data-model.md     # Phase 1 output
├── quickstart.md     # Phase 1 output
├── contracts/
│   └── api.md        # Phase 1 output — REST API contract
└── tasks.md          # Phase 2 output (/speckit-tasks)
```

### Source Code

```text
src/
├── (existing build pipeline: loader.py, renderer.py, build_runner.py, stages/)
└── web-editor/
    ├── backend/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── main.py                  # FastAPI app factory + CORS
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── infra.py             # Pydantic: TypedValue, Partition, Server, Flavour, Size, Product
    │   │   └── state.py             # Pydantic: EditorState, NodeState, ChangeState enum
    │   ├── routers/
    │   │   ├── __init__.py
    │   │   ├── tree.py              # GET /api/tree, GET /api/overview
    │   │   ├── products.py          # Product/Size/Flavour/Server CRUD
    │   │   ├── adoc.py              # GET/PUT /api/adoc/{path}
    │   │   ├── files.py             # POST /api/files/upload/{...}
    │   │   ├── units.py             # Units registry CRUD
    │   │   └── git.py               # Commit, push-retry, reset, git status
    │   └── services/
    │       ├── __init__.py
    │       ├── loader.py            # Load infra/ → EditorState (thin wrapper over src/loader.py patterns)
    │       ├── writer.py            # Write EditorState → infra/ (atomic file writes)
    │       ├── state_store.py       # Module-level singleton EditorState
    │       └── git_service.py       # GitPython wrapper (commit, push, reset, status)
    └── frontend/
        ├── Dockerfile
        ├── package.json
        ├── vite.config.js           # Proxy /api → backend:8000
        ├── index.html
        └── src/
            ├── main.js
            ├── App.vue
            ├── api/
            │   └── client.js        # Axios instance targeting backend
            ├── stores/
            │   ├── tree.js          # Pinia: tree nodes + change states
            │   └── units.js         # Pinia: units registry
            ├── components/
            │   ├── TreePanel.vue
            │   ├── MainPanel.vue
            │   ├── OverviewPanel.vue
            │   ├── CommitPanel.vue
            │   └── edit/
            │       ├── ProductEdit.vue
            │       ├── SizeEdit.vue
            │       ├── FlavourEdit.vue
            │       ├── ServerEdit.vue
            │       ├── TypedValueInput.vue
            │       └── AdocEditor.vue    # textarea + Asciidoctor.js preview toggle
            └── views/
                └── EditorView.vue

docker-compose.yml           # Repo root — justified deviation (see Complexity Tracking)

docs/
└── web-editor/
    ├── overview.md
    └── runbook.md
```

**Structure Decision**: Application code lives under `src/web-editor/` (inside the
existing `src/` tree, alongside the build pipeline code). Docker Compose lives at repo
root per FR-001. Sizing data and the new `units.json` remain in `infra/`. Documentation
goes in `docs/web-editor/`.

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| `docker-compose.yml` at repo root (not `infra/`) | FR-001 requires `docker compose up -d` from root without flags | Moving to `infra/web-editor/docker-compose.yml` forces operators to use `-f` flag, violating FR-001 |

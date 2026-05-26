# Research: Infrastructure Sizing Web Editor

**Branch**: `002-ui-client-editing` | **Date**: 2026-05-25

---

## 1. Backend In-Memory State Management

**Decision**: Module-level singleton `EditorState` object in the FastAPI process.

**Rationale**: Single-operator local tool with no auth and no session isolation requirement.
A module-level singleton is the simplest correct approach — no Redis, no DB, no session
middleware. FastAPI's uvicorn worker runs in a single process; the singleton is stable for
the container's lifetime.

**Alternatives considered**:
- Per-request state via FastAPI `Request.state`: rejected — state must survive across
  multiple HTTP requests.
- Redis-backed state: rejected — adds a third container and operational complexity for
  no benefit in a single-user local tool.

---

## 2. CORS Between FastAPI and Vite Dev Server

**Decision**: FastAPI backend on port `8000`; Vite dev server on port `5173` (Vite
default). FastAPI adds `CORSMiddleware` allowing `http://localhost:5173`. The Vite
`vite.config.js` proxies `/api/*` → `http://backend:8000` inside Docker so the
browser only talks to the Vite port and CORS is not exercised in production Docker mode.
CORS headers are still added for local development outside Docker.

**Rationale**: Proxy approach eliminates CORS issues in Docker; explicit CORS header is
a defensive fallback for developers running the frontend outside Docker.

**Alternatives considered**:
- FastAPI serving the compiled Vue SPA: rejected — the spec mandates Vite dev server
  with hot reload; no build step at container startup.

---

## 3. Asciidoctor.js in Vue 3 (FR-013a)

**Decision**: npm package `asciidoctor` (v3.x). Imported as an ES module in the
`AdocEditor.vue` component. Rendering is synchronous in the browser.

```js
import Asciidoctor from 'asciidoctor'
const asciidoctor = Asciidoctor()
const html = asciidoctor.convert(content, { safe: 'safe' })
```

The `v-html` directive binds the rendered HTML. The `safe: 'safe'` option prevents
`include::` directives from making filesystem requests in the browser.

**Rationale**: First-party official library; supports Vue 3 + Vite without extra
configuration. Synchronous render avoids async complexity in the toggle component.

**Alternatives considered**:
- `asciidoc-wasm`: smaller, but less mature and lower AsciiDoc coverage.
- Server-side render via FastAPI (return HTML from GET /api/adoc/preview): rejected —
  adds latency and a round trip for every keystroke; browser-side render is simpler.

---

## 4. GitPython for Commit / Push / Reset

**Decision**: `gitpython` (v3.x). Use `git.Repo(repo_root)` with explicit `env`
injection for SSH agent forwarding.

Key operations:
```python
from git import Repo, InvalidGitRepositoryError

repo = Repo(repo_root)

# detached HEAD check
if repo.head.is_detached:
    raise CommitBlockedError("detached HEAD")

# no remote check
has_remote = len(repo.remotes) > 0

# stage + commit
repo.git.add(A=True)   # equivalent to git add -A scoped to infra/
repo.index.commit(message, author=actor, committer=actor)

# push
origin = repo.remote("origin")
push_result = origin.push()

# retry push only
origin.push()
```

SSH agent is forwarded via `SSH_AUTH_SOCK` env var injected by Docker Compose; GitPython
inherits the container environment automatically.

**Rationale**: GitPython abstracts subprocess management and provides structured push
result inspection (to detect push failures vs auth failures).

**Alternatives considered**:
- `subprocess` calling `git` directly: more control but requires manual error parsing;
  GitPython's structured results are cleaner for push-failure detection.

---

## 5. Atomic File Writes (FR-022a)

**Decision**: Write to a sibling temp file, then `os.replace()` to the target path.
`os.replace()` is atomic on POSIX (same filesystem). The temp file is created in the
same directory as the target to guarantee same-filesystem rename.

```python
import os, tempfile, pathlib

def atomic_write(path: pathlib.Path, content: bytes) -> None:
    dir_ = path.parent
    dir_.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dir_, prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        os.unlink(tmp)
        raise
```

**Rationale**: Guarantees no partial file is visible to the filesystem even if the
process is killed mid-write. Satisfies FR-022a.

---

## 6. SSH Agent Forwarding in Docker Compose

**Decision**:

```yaml
services:
  backend:
    volumes:
      - ${SSH_AUTH_SOCK}:/ssh-agent
    environment:
      - SSH_AUTH_SOCK=/ssh-agent
```

The host's `SSH_AUTH_SOCK` socket path is mounted into the container at `/ssh-agent`.
If `SSH_AUTH_SOCK` is unset on the host, Docker Compose will log a warning and push
will fail with a clear SSH error (covered by FR-028b retry flow).

**Alternatives considered**:
- Copying SSH keys into the container: rejected — security risk; key rotation is manual.
- `ssh-agent` inside container: rejected — requires key injection at build time.

---

## 7. `infra/units.json` Initialization

**Decision**: New file `infra/units.json` — a JSON array of unit strings. The backend
seeds it with a default set if it does not exist on startup.

Default seed:
```json
["vCPU", "GB", "GiB", "TB", "TiB", "GHz", "MHz"]
```

On startup, if `infra/units.json` is missing, the backend creates it with the default
seed and marks it as a pending change (so it is committed on the next operator commit).

**Rationale**: Existing `infra/` data uses `vCPU`, `GB`, and `TB`; the seed covers all
units currently in the sample data. Operators can add/remove units from the UI.

---

## 8. Copy Semantics (FR-018)

**Decision**: Deep copy the source node (including all child nodes) in the in-memory
state. Auto-append `-copy` to the shortname if a sibling with that shortname already
exists. The new node is marked `ADDED`. The copy is in-memory only until commit.

Conflict check is recursive: if `<shortname>-copy` also conflicts, append `-copy-2`,
`-copy-3`, etc. (simple counter suffix).

---

## 9. Reset Semantics (FR-029)

**Decision**: When an operator resets a product, the backend calls the loader to re-read
that product's entire subtree from disk, replacing the in-memory `ProductNode` with a
fresh `CLEAN` node. If the on-disk files are malformed, the product node is replaced with
an error node (matching the load-time error behavior, FR-031).

All other products in `EditorState` are unaffected.

---

## 10. CI/CD (Constitution Principle IV)

Both `.gitlab-ci.yml` and `.github/workflows/` must gain a `web-editor` stage that runs:
1. Backend: `pytest src/web-editor/backend/tests/` with Python 3.11
2. Frontend: `vitest run` and `vue-tsc --noEmit`

No deployment stage (local tool). Pipeline scripts go in `src/web-editor/backend/` and
`src/web-editor/frontend/` respectively; no shared logic to extract.

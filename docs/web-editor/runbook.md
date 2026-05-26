# Infrastructure Sizing Web Editor — Runbook

## Launch

```bash
# From repo root — SSH agent must be running for git push to work
docker compose up -d

# Verify both containers are healthy
docker compose ps

# Open the editor
open http://localhost:5173   # macOS
xdg-open http://localhost:5173   # Linux
```

The backend loads `infra/` on startup. If the backend exits immediately, check logs:

```bash
docker compose logs backend
```

## Stop

```bash
docker compose down
```

Changes in `infra/` that were not committed are preserved on disk (they were never written — the editor only writes files on commit).

## SSH Agent Troubleshooting

Git push requires SSH access to the remote. The backend container uses the host SSH agent via socket forwarding.

**Check the agent is running on the host:**

```bash
echo $SSH_AUTH_SOCK   # must be non-empty
ssh-add -l            # must list at least one key
```

If `SSH_AUTH_SOCK` is empty, start the agent:

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519   # or your key path
```

**Verify the socket is accessible inside the container:**

```bash
docker compose exec backend ls -la /ssh-agent
docker compose exec backend ssh-add -l
```

If the socket path changed (e.g., after system restart), restart the containers:

```bash
docker compose down && docker compose up -d
```

## Inspect Container Logs

```bash
# Live tail
docker compose logs -f backend
docker compose logs -f frontend

# Last 100 lines
docker compose logs --tail=100 backend
```

Common backend log patterns:

| Log message | Meaning |
|-------------|---------|
| `Loading infra/...` | Startup load in progress |
| `units.json not found — seeding defaults` | New repo, units.json created on next commit |
| `Product {sn} load error: ...` | Malformed JSON in that product; node shown with ERROR state |

## Recover from a Failed Push

If the editor shows "Retry Push" it means the local `git commit` succeeded but `git push` failed (network issue, remote rejected, etc.).

**Option 1 — Retry from the UI:** Click "Retry Push" in the Commit panel.

**Option 2 — Push manually from the host:**

```bash
# Identify the commit SHA from the UI error message or:
git log --oneline -3

git push origin HEAD
```

**Option 3 — Push from inside the backend container:**

```bash
docker compose exec backend bash
cd /repo
GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=no" git push origin HEAD
```

## Rebuild Containers

If you change backend or frontend source code outside the editor:

```bash
docker compose build
docker compose up -d
```

## Ports

| Service  | Host port | Container port |
|----------|-----------|----------------|
| Frontend | 5173      | 5173           |
| Backend  | 8000      | 8000           |

The frontend Vite dev server proxies `/api` requests to the backend. Do not call `:8000` directly from the browser in normal use.

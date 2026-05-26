# Quickstart: Infrastructure Sizing Web Editor

## Prerequisites

- Docker and Docker Compose v2 installed on the host
- Repository cloned to the host machine
- SSH agent running on the host with your key loaded (`ssh-add`) — required for git push

## Launch

```bash
docker compose up -d
```

The command starts two containers:
- **backend** — FastAPI on `http://localhost:8000`
- **frontend** — Vite dev server on `http://localhost:5173`

Open `http://localhost:5173` in a desktop browser.

On first launch with no `infra/units.json`, the backend creates it automatically with
default units (`vCPU`, `GB`, `GiB`, `TB`, `TiB`, `GHz`, `MHz`).

## First Edit Cycle

1. **Navigate**: The left panel shows the full product tree. Click any node to open its
   edit fields on the right.

2. **Edit**: Change field values directly. Changes are held in memory — no file is
   modified yet. Modified nodes show a blue dot indicator; the node is not saved to disk.

3. **Add a child entity**: Hover any parent node in the tree and click the `+` icon to
   add a child (size → product, flavour → size, server → flavour).

4. **Copy a flavour**: Right-click (or use the context menu) on any flavour node and
   select **Copy**. Navigate to the target size node and select **Paste**.

5. **Delete a node**: Right-click a node and select **Delete**, then confirm. The node
   remains visible with strikethrough text (red) until the next commit.

6. **Edit AsciiDoc**: Click a `prefix` or `suffix` node under a product or flavour.
   The right panel shows a plain text editor. Use the **Preview** toggle to render the
   AsciiDoc content as HTML.

## Commit

1. Click **Commit** in the top bar to open the commit panel.
2. Review the flat list of changed entities/files displayed in the panel.
3. Enter a commit message.
4. Click **Commit & Push**.
   - If push succeeds: all changed files are on disk, a commit is created, and the branch
     is pushed to the configured remote.
   - If push fails: an error banner appears with a **Retry Push** button. The local commit
     is already created and safe.
   - If no remote is configured: the commit is created locally and you are informed that
     push was skipped.

## Reset a Product

To discard all in-memory changes for a specific product:
1. Click the product node in the tree.
2. Click **Reset Product** in the edit panel header.
3. Confirm the prompt. All changes to that product revert to the on-disk state.

## Manage Units

1. Open **Settings → Units Registry** from the top nav.
2. Add a new unit by typing in the input field and clicking **Add**.
3. Delete a unit by clicking the trash icon — a warning lists all TypedValues that will
   be invalidated. Confirm to proceed.

## Stop

```bash
docker compose down
```

In-memory state that has not been committed is lost on container shutdown.

# Feature Specification: Infrastructure Sizing Web Editor

**Feature Branch**: `002-ui-client-editing`

**Created**: 2026-05-25

**Status**: Draft

---

## Clarifications

### Session 2026-05-25

- Q: Where is the units registry stored and persisted? → A: `infra/units.json` in the repository; committed alongside infrastructure data via the normal commit flow.
- Q: When the user navigates to a different tree node while the current node has edits, what happens? → A: Changes are automatically applied to the in-memory state; no prompt is shown.
- Q: Does the commit action also push to the remote, or is push separate? → A: The UI provides two buttons: "Commit & Push" (commit then push in one action) and "Commit Only" (commit locally without pushing). Both share the same commit message field.
- Q: When a copied entity's shortname conflicts with an existing sibling, what happens? → A: The editor auto-appends `-copy` to the shortname; the user can rename it in the edit panel afterwards.
- Q: What tech stack should the web editor use? → A: Python (FastAPI) backend + Vue.js frontend.
- Q: How should the editor handle a malformed `servers.json` at load time? → A: Show a scoped error banner for that product in the tree; all other products remain editable normally.
- Q: When a new entity's shortname conflicts with an existing sibling on add, what happens? → A: Show an inline validation error on the shortname field immediately; the user cannot save or navigate away until a unique shortname is entered.
- Q: How should the editor behave when the `infra/` directory is empty (no products defined yet)? → A: Show an empty state in the tree panel with a prominent "Add first product" action; the main panel shows a welcome/getting-started message.
- Q: What should the editor do when the git repository is in a detached HEAD state and the user attempts to commit? → A: Show an error and prevent the commit; display a message instructing the user to `git checkout <branch>` before committing.
- Q: When a unit is deleted from the registry and TypedValues currently reference that unit, what happens to those TypedValues? → A: Affected TypedValues are immediately marked as invalid in the tree and edit panel; the user must select a replacement unit before committing.
- Q: When a file upload fails mid-operation (disk full, permission denied), what should the editor do? → A: Atomic upload — show an error banner in the flavour panel and guarantee no partial file is left on disk.
- Q: Should the Vue.js frontend be served as a pre-built static SPA or as a Vite dev server inside Docker? → A: Vite dev server with hot reload; no build step at container startup.
- Q: Does the editor require keyboard navigation or accessibility support? → A: Basic keyboard navigation — Tab through fields, Enter to confirm, Escape to cancel/close dialogs.
- Q: Should moving an entity to a different parent be supported, or is copy-then-delete the intended workflow? → A: Copy-then-delete is sufficient for v1; no dedicated move/drag-and-drop operation.
- Q: When a node is deleted in-memory before commit, how should it appear in the tree? → A: Remain visible in the tree with strikethrough text and a red/warning color indicator (pending deletion); undo is available via the product-level reset action.
- Q: Should the commit panel show a summary of pending changes before executing the commit? → A: Yes — the commit panel MUST display a flat list of changed entity/file names; no diff details or change type breakdown is shown.
- Q: If the git push fails after the local commit is already created, what should the editor do? → A: Show an error message and offer a "Retry Push" button; the local commit is preserved and the operator can retry push from the UI without re-entering the commit message.
- Q: What component should the integrated editor use for .adoc files, and is a preview needed? → A: Plain textarea; a toggle/button to render the AsciiDoc content as a HTML preview MUST also be provided alongside the textarea.
- Q: Should the overview panel reflect in-memory counts or on-disk counts? → A: In-memory counts — the overview MUST reflect all uncommitted adds and deletes in real time, consistent with the current tree state.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Navigate the Tree and Edit Any Entity (Priority: P1)

An operator opens the web editor and sees the full infrastructure hierarchy in a tree on
the left side of the screen (products → sizes → flavours → servers). Clicking any node in
the tree selects it and reveals the relevant edit fields in the main panel on the right.
The operator edits fields directly in the panel. All changes are held in memory until
the operator explicitly commits. New items (products, sizes, flavours, servers) can be
added from the tree using an inline add action on any parent node.

**Why this priority**: The tree + selection paradigm is the core interaction model of the
entire editor. Every other feature depends on it.

**Independent Test**: Launch the editor, confirm the tree is populated with existing
products. Click a flavour node — confirm server fields appear on the right. Edit a CPU
value — confirm the field updates in the panel. Confirm no file on disk has changed yet.

**Acceptance Scenarios**:

1. **Given** the editor is running and products exist, **When** the user opens the editor, **Then** all products are shown as nodes in the tree, with sizes, flavours, and servers expandable beneath them.
2. **Given** the tree is visible, **When** the user clicks any node, **Then** the main panel shows all editable fields for that node, populated with current values.
3. **Given** a field is edited in the main panel, **When** the user changes a value, **Then** the change is reflected immediately in the panel and the node is marked as having unsaved changes, but no file on disk is modified.
4. **Given** a parent node is selected (e.g., a size), **When** the user triggers "Add" on it, **Then** a new child entity (e.g., a flavour) is created in the tree with default values and selected for editing.

---

### User Story 2 — Overview Dashboard (Priority: P1)

An operator opens the editor and immediately sees a summary overview of the entire
infrastructure: how many products are defined, their sizes, flavour counts, and server
totals. The overview gives a at-a-glance health check of the data before editing begins.

**Why this priority**: Without an overview, operators must expand every node in the tree to
understand the scope of the data. The overview dramatically reduces the time to orient.

**Independent Test**: Load the editor with a repository that has two products of different
sizes. Confirm the overview lists both products with their correct size, flavour, and server
counts.

**Acceptance Scenarios**:

1. **Given** the editor loads, **When** no node is selected in the tree, **Then** the main panel shows an overview listing all products with their size, flavour, and server counts.
2. **Given** the overview is visible, **When** the user clicks on a product name in the overview, **Then** that product node is selected in the tree and its detail is shown in the main panel.

---

### User Story 3 — Add, Copy, and Delete Entries (Priority: P2)

An operator needs to replicate an existing infrastructure entry (e.g., copy a flavour from
one size to another) or add a fresh entry at any level of the hierarchy. They can also
delete entries they no longer need, with a confirmation step. All operations are in-memory
until commit.

**Why this priority**: Copy and delete accelerate the authoring workflow significantly —
copying an existing flavour is faster than creating one from scratch, and bulk deletion
needs a safe workflow.

**Independent Test**: Copy a flavour from one size, paste it under a different size, verify
that it appears with the copied servers. Delete a server, verify it is removed from the
in-memory state. Commit and verify the files reflect both operations.

**Acceptance Scenarios**:

1. **Given** any entity exists in the tree, **When** the user copies it and pastes it under a compatible parent, **Then** a duplicate of that entity (and all its children) appears in the tree, ready to be renamed/edited.
2. **Given** an entity exists, **When** the user deletes it and confirms the prompt, **Then** it is removed from the in-memory state and the tree, and marked as deleted for the next commit.
3. **Given** a copy is in progress, **When** the user pastes into an incompatible parent (e.g., a server into a product), **Then** the paste action is disabled or an error message is shown.

---

### User Story 4 — Edit AsciiDoc Files with Integrated Editor (Priority: P2)

An operator selects a product-level prefix, product-level suffix, or flavour-level
prefix/suffix in the tree. The main panel shows an integrated text editor with the
current content of that `.adoc` file. The operator edits the AsciiDoc markup directly,
and the change is held in memory until commit.

**Why this priority**: The `.adoc` files (prefix, suffix) are first-class content in
every rendered PDF. They must be editable from the same tool, not via a separate text
editor session.

**Independent Test**: Open a product's prefix in the editor, change a sentence, commit,
and verify the `.adoc` file on disk has the updated content.

**Acceptance Scenarios**:

1. **Given** a product or flavour has a prefix or suffix file, **When** the user selects it in the tree, **Then** a text editor opens in the main panel with the current file content.
2. **Given** the text editor is open, **When** the user edits the content and the change is committed, **Then** the corresponding `.adoc` file on disk is updated.
3. **Given** the `.adoc` file does not yet exist, **When** the user selects the prefix/suffix node, **Then** the editor opens with empty content and creates the file on commit.

---

### User Story 5 — Upload Files (Priority: P3)

An operator wants to attach an image (e.g., an architecture diagram PNG) or a Mermaid
diagram file to a flavour. They use a file upload control in the flavour's edit panel to
select and upload the file. The file is stored in the flavour's directory on the host and
the flavour's image reference is updated in memory.

**Why this priority**: Diagrams are optional enrichment. The core editing workflow works
without them; upload is a convenience feature.

**Independent Test**: Open a flavour, upload a PNG file, confirm it appears in the flavour
directory on the host, and confirm the `meta.json` image reference is updated after commit.

**Acceptance Scenarios**:

1. **Given** a flavour is selected, **When** the user uploads a valid image file (PNG, SVG) or Mermaid file (.mmd), **Then** the file is saved to the flavour directory immediately and the image reference is set in memory.
2. **Given** an unsupported file type is uploaded, **When** the user attempts the upload, **Then** an error is shown and the upload is rejected.

---

### User Story 6 — Manage Centrally Defined Units (Priority: P3)

An operator can view and manage the registry of available units (e.g., vCPU, GB, TB, GHz,
GiB). When editing TypedValue fields (CPU, memory, disk partition size), the unit field
offers only values from this registry. An operator can add a new unit to the registry so
it becomes available across all TypedValue fields in the editor.

**Why this priority**: Without a central unit registry, operators type units as free text
and introduce inconsistencies (e.g., "GB" vs "GiB" vs "Gb"). Centralising units enforces
consistency across all infrastructure entries.

**Independent Test**: Add "PiB" as a new unit, then open a disk partition size field and
confirm "PiB" appears as an option. Remove a unit and confirm it no longer appears.

**Acceptance Scenarios**:

1. **Given** the units registry is open, **When** the user adds a new unit, **Then** it becomes available as a selectable option in all TypedValue unit fields.
2. **Given** a TypedValue field is being edited, **When** the user opens the unit selector, **Then** only units from the registry are shown (no free-text entry allowed).
3. **Given** a unit is in use by at least one entity, **When** the user attempts to delete it, **Then** a warning is shown listing the affected entities before deletion is confirmed.

---

### User Story 7 — Commit and Reset Changes (Priority: P1)

An operator who has finished editing in memory can commit all pending changes: the editor
writes all modified JSON and `.adoc` files to disk and creates a git commit with a
user-supplied message. If the operator wants to discard changes for a specific folder (e.g.,
undo all edits made to one product), they can reset that folder's in-memory state back to
the on-disk state, without affecting changes made to other products.

**Why this priority**: The commit is the only moment changes reach disk. A clean,
reliable commit + selective reset is essential to the safety of the tool.

**Independent Test**: Make edits to two products. Reset one product's changes — confirm its
in-memory state reverts to what's on disk while the other product's edits remain. Commit —
confirm only the second product's files are written and the commit appears in `git log`.

**Acceptance Scenarios**:

1. **Given** in-memory changes exist, **When** the user commits with a message, **Then** all changed JSON and `.adoc` files are written to disk, a git commit is created, and the commit is pushed to the configured remote.
2. **Given** in-memory changes exist for multiple products, **When** the user resets a specific product's folder, **Then** only that product's changes are discarded; other products' changes remain.
3. **Given** no remote is configured, **When** the user commits, **Then** the commit is created locally and the user is informed that push was skipped.
4. **Given** no in-memory changes exist, **When** the user opens the commit panel, **Then** the commit button is disabled and a "nothing to commit" message is shown.

---

### Edge Cases

- When a `servers.json` file is malformed (invalid JSON) at load time, the affected product node is marked with a scoped error indicator in the tree; the user cannot edit that product until the file is fixed outside the editor. All other products load and remain fully editable.
- When a shortname for a new entity conflicts with an existing sibling (directory name), the editor shows an inline validation error on the shortname field immediately; the user cannot save or navigate away until a unique shortname is entered.
- When the `infra/` directory is empty, the tree panel shows an empty state with a prominent "Add first product" action; the main panel shows a welcome/getting-started message.
- When the git repository is in a detached HEAD state and commit is attempted, the editor shows an error and prevents the commit; the user is instructed to `git checkout <branch>` before retrying.
- When a unit is deleted from the registry while TypedValues reference it, those TypedValues are immediately marked as invalid in the tree and edit panel; the user must select a replacement unit before the commit action is allowed.
- When a file upload fails mid-operation (disk full, permission denied, etc.), the upload is treated as atomic: no partial file is left on disk and an error banner is shown in the flavour edit panel.
- Copied entities with conflicting shortnames are automatically renamed with a `-copy` suffix at paste time; the user renames in the edit panel if needed.
- If the container is restarted before commit, all in-memory changes are lost. This is acceptable for a local operator tool.

---

## Requirements *(mandatory)*

### Functional Requirements

**Navigation and Layout**

- **FR-001**: The editor MUST be launchable with a single `docker compose up -d` command from the repository root.
- **FR-002**: The editor MUST be accessible from a browser on the host machine without additional installation.
- **FR-003**: The editor MUST present a persistent tree panel showing the full hierarchy: products → sizes → flavours → servers.
- **FR-004**: Clicking any node in the tree MUST select it and display all editable fields for that node in the main panel.
- **FR-005**: When no node is selected, the main panel MUST display an overview of all products (sizes, flavour count, server count per product); all counts MUST reflect the current in-memory state, including uncommitted adds and deletes.

**Editing**

- **FR-006**: Users MUST be able to edit all server fields: system name, count, CPU (TypedValue), CPU clocking, memory (TypedValue), disk partitions, network items, software items, and comment.
- **FR-007**: The editor MUST support both static TypedValues (numeric value + unit from registry) and dynamic TypedValues (formula string + unit from registry) for CPU, memory, and disk partition size.
- **FR-008**: Users MUST be able to edit product metadata: display name. Shortname is set only when creating a new product (ADDED state) and is read-only for existing products (shortname = directory key; renaming is out of scope for v1).
- **FR-009**: Users MUST be able to edit size metadata: display name. Shortname is set only when creating a new size (ADDED state) and is read-only for existing sizes. Size-level prefix and suffix content is stored as standalone `prefix.adoc` / `suffix.adoc` files in the size directory and is editable via the AsciiDoc editor (FR-013) when those nodes are selected in the tree.
- **FR-010**: Users MUST be able to edit flavour metadata: display name and image reference. Shortname is set only when creating a new flavour (ADDED state) and is read-only for existing flavours.
- **FR-011**: All edits MUST be held in memory; no file on disk is modified until the user explicitly commits. (Exception: binary file uploads per FR-021 are written to disk immediately as they are not part of the in-memory JSON model.)
- **FR-011a**: When the user navigates to a different tree node, any edits on the current node are automatically applied to the in-memory state without prompting.
- **FR-012**: Nodes with in-memory changes MUST be visually distinguished in the tree (e.g., marked as modified).

**AsciiDoc Editor**

- **FR-013**: Product-level and flavour-level prefix and suffix `.adoc` files MUST be selectable in the tree and editable via a plain textarea in the main panel.
- **FR-013a**: The AsciiDoc editor panel MUST provide a toggle to switch between edit mode (plain textarea) and preview mode (AsciiDoc content rendered as HTML using Asciidoctor.js in the browser).
- **FR-014**: The AsciiDoc editor MUST preserve the full file content without stripping or transforming markup.

**Adding and Removing Entities**

- **FR-015**: Users MUST be able to add new child entities from any parent node in the tree (add size to product, add flavour to size, add server to flavour).
- **FR-016**: Users MUST be able to add a new product from the tree root level.
- **FR-017**: Users MUST be able to delete any entity from the tree, with a confirmation prompt; deletion is in-memory until commit.
- **FR-017a**: Nodes deleted in memory MUST remain visible in the tree with strikethrough text and a red/warning color indicator; they MUST be removed from the tree only after the next successful commit. Operators can undo a pending deletion via the product-level reset action.
- **FR-018**: Users MUST be able to copy an existing entity (and all its children) and paste it under a compatible parent node; if the shortname conflicts with an existing sibling, the editor automatically appends `-copy` to the shortname. If the `-copy` shortname also conflicts, the editor auto-increments with a numeric suffix (`-copy-2`, `-copy-3`, etc.) until a unique name is found.
- **FR-019**: The editor MUST validate required fields (non-empty system name, at least one disk partition per server) before allowing commit.

**File Upload**

- **FR-020**: Users MUST be able to upload a file (PNG, SVG, or `.mmd`) to a flavour's directory directly from the flavour edit panel.
- **FR-021**: Uploaded files MUST be written to the flavour directory on the host immediately (not deferred to commit).
- **FR-022**: The editor MUST reject file uploads with unsupported types and display an error.
- **FR-022a**: File uploads MUST be atomic: if the write fails for any reason (disk full, permission denied), no partial file is left on disk and an error banner is shown in the flavour edit panel.

**Units Registry**

- **FR-023**: The editor MUST maintain a central registry of available units (e.g., vCPU, GB, GHz) stored in `infra/units.json` in the repository.
- **FR-024**: All TypedValue unit fields MUST offer only values from the units registry (no free-text unit entry).
- **FR-025**: Users MUST be able to add new units to the registry from a dedicated settings area; changes are held in memory and written to `infra/units.json` on commit.
- **FR-026**: Users MUST be able to delete units from the registry; if a unit is in use, a warning listing affected entities MUST be shown before deletion proceeds. Upon confirmation, affected TypedValues MUST be immediately marked as invalid in the tree and edit panel; the user MUST select a replacement unit for each before the commit action is allowed.

**Accessibility**

- **FR-035**: The editor MUST support basic keyboard navigation: Tab moves focus between interactive elements, Enter confirms the focused action, and Escape cancels or closes the active dialog/panel. Full WCAG compliance is out of scope for v1.

**Commit and Reset**

- **FR-027**: Users MUST be able to commit all in-memory changes with a custom message. Two commit actions are available: "Commit & Push" (writes files, creates a git commit, and pushes to the remote) and "Commit Only" (writes files and creates a git commit without pushing). Both actions are available from the commit panel.
- **FR-027a**: Before the commit is executed, the commit panel MUST display a flat list of the names of all changed entities/files; no diff details or change-type breakdown (added/modified/deleted) is shown.
- **FR-028**: The commit-and-push operation MUST use the host SSH agent forwarded into the container via Docker Compose.
- **FR-028a**: If no remote is configured, the action MUST commit locally and inform the user that push was skipped.
- **FR-028b**: If push fails after the local commit is created (e.g., SSH auth error, network timeout), the editor MUST display an error message and present a "Retry Push" button; the local commit MUST be preserved so the operator can retry push from the UI without data loss.
- **FR-029**: Users MUST be able to reset the in-memory state for a specific product folder, reverting it to the on-disk state without affecting other products.
- **FR-030**: The UI MUST display a clear error message when a commit operation fails, including the reason.
- **FR-031**: When a `servers.json` file is malformed at load time, the editor MUST display a scoped error indicator on that product's tree node and prevent editing of that product; all other products MUST remain fully editable.
- **FR-032**: When a user enters a shortname for a new entity that conflicts with an existing sibling, the editor MUST show an inline validation error on the shortname field immediately and prevent saving or navigating away until a unique shortname is provided.
- **FR-033**: When the `infra/` directory is empty on load, the tree panel MUST show an empty state with a prominent "Add first product" action; the main panel MUST show a welcome/getting-started message.
- **FR-034**: When the git repository is in a detached HEAD state, the commit action MUST be blocked; the UI MUST show an error message instructing the user to `git checkout <branch>` before committing.

### Key Entities

- **Product**: shortname (directory key), display name; references sizes registry.
- **Size**: shortname, display name, optional prefix/suffix `.adoc` files (stored as `prefix.adoc` / `suffix.adoc` in the size directory); belongs to a product.
- **Flavour**: shortname, display name; belongs to a size; has optional image (file or mermaid) and prefix/suffix adoc files.
- **Server**: system name, count, CPU (TypedValue), CPU clocking, memory (TypedValue), disk partitions, network items, software items, comment.
- **Partition**: size (TypedValue), performance, comment/usage.
- **TypedValue**: discriminated union — static (numeric value + unit) or dynamic (formula string + unit).
- **UnitsRegistry**: shared list of unit strings stored in `infra/units.json`; available for selection in all TypedValue unit fields; committed with infrastructure data.
- **AdocFile**: content of a `.adoc` file (prefix or suffix) associated with a product or flavour.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An operator can launch the editor and make a first edit within 2 minutes of cloning the repository (no prior setup beyond Docker).
- **SC-002**: The full infrastructure hierarchy is visible in the tree within 3 seconds of the editor loading.
- **SC-003**: A full CRUD cycle (create product → add server → edit fields → copy flavour → delete original → commit) completes without leaving orphan files or corrupt JSON on disk.
- **SC-004**: The commit flow (enter message → click commit → files written → git commit created) completes within 5 seconds for a typical change set (≤ 20 modified files).
- **SC-005**: Resetting a folder's changes restores the in-memory state to match the on-disk state in under 1 second, without affecting other products.
- **SC-006**: All validation errors are shown inline without losing the user's in-memory edits.
- **SC-007**: The overview panel loads and displays accurate counts for all products within 2 seconds of the editor opening.

---

## Assumptions

- The repository is cloned to the host machine and the operator has Docker and Docker Compose installed.
- The host SSH agent is running and its socket path is available as `SSH_AUTH_SOCK`; Docker Compose forwards this into the container.
- The editor does not need user authentication — it is a local developer/operator tool, not a public-facing service.
- The host directory is mounted read-write into the container.
- In-memory state is ephemeral: if the container restarts before commit, all uncommitted changes are lost. This is acceptable for a local tool.
- File uploads (images, mermaid files) are written to disk immediately since they are binary/static assets that are not part of the in-memory JSON model.
- Mobile browser support is out of scope; the editor targets desktop browsers only.
- The editor supports basic keyboard navigation: Tab moves focus between fields, Enter confirms actions, and Escape cancels or closes dialogs. Full WCAG compliance is out of scope for v1.
- The editor does not render PDF previews — that remains the responsibility of the existing `build.py` pipeline.
- The `infra/` directory structure follows the conventions defined in `docs/infra-sizing-doc-export/file-structure.md`.
- The web editor uses a **Python (FastAPI) backend** serving a REST API and a **Vue.js frontend** served via a **Vite dev server** (hot reload enabled, no build step at container startup). A dedicated `docker-compose.yml` launches both services; the Vite dev server runs inside Docker and is accessible from the host browser.
- Concurrent edits from multiple users are out of scope for v1; the tool is intended for single-operator use.
- Moving an entity to a different parent (cut + paste or drag-and-drop) is out of scope for v1; the copy-then-delete workflow is the intended approach.
- The units registry is stored in `infra/units.json` and is part of the repository; unit changes are committed via the same commit flow as infrastructure data.

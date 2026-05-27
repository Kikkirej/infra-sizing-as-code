# Feature Specification: Product Version Management

**Feature Branch**: `004-product-versioning`

**Created**: 2026-05-26

**Status**: Draft

**Input**: User description: "versioning of product infrastructure. Each product has a version specific file. File structure is a JSON list with changes. Each change has a author, Version name (can be updated) and a date. When a product is released, the versions will be part of the generated PDF, it will be tagged (productshortname-version). After the release a new version will be created, first version entry is copying data from version "previous version". The version.jsons are in its own folder (versioning) in the product. Active version is wip.json, released versions are stored as "<version>.json", Author must be in format "[Firstname], [Lastname]" verified by regex. Whenever a commit for a product is commited, it should ask whether a version note should be made. Versions should be visible in a table in a own tree entry under product, which shows a table and offers crud operations. Multiple authors seperated by semicolons are also possible."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Version History (Priority: P1)

A user opens a product in the web editor and sees a dedicated "Versions" entry in the product tree. Clicking it opens a panel showing a version selector, a `version_name` field above the table, and the change entries for the selected version. The user can switch between WIP and any released version; the `version_name` field and entries are editable only for WIP.

**Why this priority**: This is the foundational read path. All other versioning capabilities depend on being able to see and navigate version data.

**Independent Test**: Can be fully tested by opening a product that already has a `versioning/wip.json` file and verifying the table renders with all entries.

**Acceptance Scenarios**:

1. **Given** a product with a `versioning/wip.json` containing multiple entries, **When** the user clicks the "Versions" tree entry, **Then** the WIP version is selected by default and its entries are shown in the table with columns for author(s) and date.
2. **Given** a product with no `versioning/` folder, **When** the user clicks the "Versions" tree entry, **Then** an empty table is shown with an option to add the first entry.
3. **Given** a product with both WIP and released version files, **When** the user selects a released version from the version selector, **Then** that version's entries are shown in a read-only table.
4. **Given** the user is viewing a released version, **When** they attempt to edit or delete an entry, **Then** the action is blocked and the entries remain read-only.

---

### User Story 2 - Manage Version Entries (Priority: P1)

A user can create, edit, and delete individual version change entries in the WIP version table. Each entry requires a valid author name and a date; an optional notes field is also available. Multiple authors can be listed separated by semicolons. The shared `version_name` for the entire WIP version is edited via the standalone field above the table.

**Why this priority**: CRUD operations on version entries are the core of the feature — without them users cannot build up the version history that feeds into PDFs and releases.

**Independent Test**: Can be fully tested by adding, editing, and deleting entries in the WIP version table and confirming the backing `wip.json` is updated accordingly.

**Acceptance Scenarios**:

1. **Given** the Versions table is open with WIP selected, **When** the user clicks "Add Entry" and fills in a valid author (`Firstname, Lastname`) and date, **Then** the entry is saved to `wip.json` and appears in the table.
2. **Given** the WIP version is selected, **When** the user edits the `version_name` field above the table, **Then** the change is saved and applied to the entire `wip.json`.
3. **Given** an existing entry, **When** the user enters an author in an invalid format (e.g., `JohnDoe` or `John Doe`), **Then** a validation error is shown and the entry is not saved.
4. **Given** an existing entry, **When** the user enters multiple authors as `Firstname, Lastname; Firstname2, Lastname2`, **Then** the entry is accepted and saved correctly.
5. **Given** an existing entry, **When** the user deletes it, **Then** it is removed from `wip.json` and disappears from the table.

---

### User Story 3 - Release a Product Version (Priority: P2)

When a user releases a product, the current WIP version is finalized: it is saved as a named version file, included in the generated PDF, and the repository is tagged with `productshortname-version`. Before finalizing, the system shows a popup asking for the new WIP version name. A new `wip.json` is then automatically created with that version name and one seeded entry whose author and date are copied from the last entry of the just-released version and whose notes text reads "copied from previous version".

**Why this priority**: Releasing is the point at which version history becomes part of the permanent record. It is the business trigger that makes versioning valuable.

**Independent Test**: Can be fully tested by triggering a product release and verifying the named version file is created, the PDF includes the version table, the git tag exists, and a fresh `wip.json` is present with the seeded first entry.

**Acceptance Scenarios**:

1. **Given** a product with a populated `wip.json`, **When** the user releases the product, **Then** `wip.json` is renamed/copied to `<version>.json` in the `versioning/` folder.
2. **Given** a release action completes, **When** the PDF is generated, **Then** the version history table from the released version file is included in the document.
3. **Given** a release action completes, **When** the repository is inspected, **Then** a git tag named `<productshortname>-<version>` exists pointing to the release commit.
4. **Given** the release popup is shown, **When** the user enters a new version name and confirms, **Then** a new `wip.json` is created with that version name and one seeded entry: author and date copied from the last entry of the just-released version, notes text set to "copied from previous version".

---

### User Story 4 - Version Note Prompt on Commit (Priority: P3)

Whenever the user commits changes to a product, the system prompts them to optionally add a version note entry to the active WIP version. They can provide author(s), a version name, and a date, or skip the prompt.

**Why this priority**: This improves changelog hygiene without blocking workflow. It is additive and can be skipped, making it a lower-risk enhancement.

**Independent Test**: Can be fully tested by committing a product change, confirming the prompt appears, submitting a new entry, and verifying it is appended to `wip.json`.

**Acceptance Scenarios**:

1. **Given** the user commits changes to a product, **When** the commit process is initiated, **Then** a prompt appears asking whether a version note should be added.
2. **Given** the version note prompt is shown, **When** the user provides a valid author, version name, and date and confirms, **Then** a new entry is appended to `wip.json`.
3. **Given** the version note prompt is shown, **When** the user skips it, **Then** the commit proceeds without modifying `wip.json`.
4. **Given** the version note prompt is shown, **When** the user enters an invalid author format, **Then** a validation error is shown before the entry can be saved.

---

### Edge Cases

- **If `versioning/wip.json` is malformed or has an unexpected structure**: the Versions panel shows an error state with a "Reset to empty WIP" button. Clicking it creates a fresh, valid `wip.json` with the current WIP version name (if recoverable) or an empty version name. Silent auto-repair is not performed.
- **If `wip.json` has no entries at release time**: the release is blocked with an error: "Cannot release a version with no change entries."
- **If a released version file with the same `version_name` already exists**: the release is blocked with an error message: "Version X already exists. Please change the WIP version name." The user must update the WIP `version_name` before retrying.
- What if the author field contains only one name part (missing comma separator)?
- **If multiple semicolon-separated authors contain inconsistent formatting**: the entire author field is rejected and the validation message lists each invalid author by value (e.g., "Invalid authors: 'JohnDoe', 'Jane'"). The field is not saved until all authors pass validation.
- How does the version table behave when a product has many (50+) version entries?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each product MUST have a dedicated `versioning/` subdirectory that stores its version files.
- **FR-002**: The active (in-progress) version MUST be stored as `versioning/wip.json`, a JSON array of change entries.
- **FR-003**: Each change entry MUST contain: author(s), date, and an optional free-text notes field. All entries within a single version file share one common `version_name` that identifies the version as a whole.
- **FR-004**: Author MUST be validated against the format `Firstname, Lastname` (single author) or multiple authors separated by semicolons (e.g., `Firstname, Lastname; Firstname2, Lastname2`).
- **FR-005**: The `version_name` MUST be displayed as a standalone editable text field above the entries table in the Versions panel. It is editable only when the WIP version is selected; it is read-only for released versions. The value MUST be validated to contain only alphanumeric characters, dots, hyphens, and underscores (regex: `^[A-Za-z0-9._-]+$`).
- **FR-006**: Released version files MUST be stored as `versioning/<version>.json`, where `<version>` is the single `version_name` shared across all entries in the released `wip.json`.
- **FR-007**: When a product is released and PDF generation is performed, the system MUST include the version history table from the released version file in the generated document. If asciidoctor is unavailable at runtime, PDF generation is skipped and the release response includes `"pdf_generated": false`; the remaining release steps (version file, git tag, new wip.json) are unaffected.
- **FR-008**: When a product is released, the system MUST create a git tag named `<productshortname>-<version>`, where `<version>` is the shared `version_name` of the released `wip.json`.
- **FR-009**: At release time, the system MUST present a popup asking the user for the new WIP version name before finalizing the release.
- **FR-010**: After a release, the system MUST automatically create a new `versioning/wip.json` using the version name from the release popup, with one seeded entry: author and date copied from the last entry of the just-released version, notes text set to "copied from previous version".
- **FR-011**: The web editor MUST display a "Versions" entry in the product tree, which opens a panel containing a version selector and a table of entries for the selected version.
- **FR-012**: The version selector MUST list all available versions (WIP and released); WIP is selected by default.
- **FR-013**: The Versions table MUST support full CRUD operations (create, read, update, delete) when the WIP version is selected. Released versions are read-only.
- **FR-014**: When committing product changes, the system MUST prompt the user to optionally add a version note to `wip.json`.
- **FR-015**: The system MUST reject author values that do not match the required format and display a clear validation message.
- **FR-016**: If a released version file named `versioning/<version>.json` already exists at release time, the system MUST block the release and display an error: "Version \<version\> already exists. Please change the WIP version name."
- **FR-017**: If `wip.json` contains no entries at release time, the system MUST block the release and display an error: "Cannot release a version with no change entries."
- **FR-018**: If `wip.json` is malformed or structurally invalid, the Versions panel MUST display an error state with a "Reset to empty WIP" button. Activating it replaces the file with a fresh valid `wip.json`. Silent auto-repair is not permitted.
- **FR-019**: The `version_name` field MUST be validated against the pattern `^[A-Za-z0-9._-]+$`. Values that fail this check MUST be rejected with a clear validation message before saving or releasing.
- **FR-020**: When the author field contains multiple semicolon-separated values and one or more fail format validation, the entire field MUST be rejected. The validation message MUST identify each invalid author by value (e.g., "Invalid authors: 'JohnDoe', 'Jane'").

### Key Entities

- **VersionEntry**: Represents a single change record within a version. Attributes: author(s) (string, validated), date (date value), notes (optional free-text string). Does not carry an individual version_name — the version_name is a shared property of the containing version file.
- **WIPVersion**: The current in-progress version of a product, stored as `versioning/wip.json`. Has a single shared `version_name` (the intended release version identifier) and an ordered list of `VersionEntry` items.
- **ReleasedVersion**: A finalized, immutable version of a product stored as `versioning/<version>.json`. Created from the WIP version at release time.
- **Product**: An infrastructure product that owns a `versioning/` directory and zero or more released versions plus one active WIP version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add, edit, or delete a version entry within 30 seconds without leaving the web editor.
- **SC-002**: All released PDFs include the complete version history table from the corresponding released version file.
- **SC-003**: 100% of release actions result in a correctly named git tag and a freshly seeded `wip.json`.
- **SC-004**: Invalid author formats are caught before saving, with zero invalid entries persisted to any version file.
- **SC-005**: The version note commit prompt appears on every product commit, and skipping it does not delay the commit by more than 2 seconds.
- **SC-006**: Users can navigate from the product tree to the Versions table in a single click.

## Clarifications

### Session 2026-05-26

- Q: How is the release version identifier determined (for git tag and `<version>.json` filename)? → A: All change entries in `wip.json` share one `version_name`; that single shared value is used as the release identifier.
- Q: Should the Versions panel show only WIP or also released versions? → A: One version at a time — a version selector lets the user switch between WIP and released versions; only WIP is editable.
- Q: What data is seeded into the new `wip.json` after release, and how is the new version name determined? → A: One entry with author + date from the last entry of the released version and notes text "copied from previous version"; version name for the new WIP is entered by the user in a popup at release time.
- Q: Should the commit-time version note prompt apply in the web editor only, or also via git CLI hook? → A: Web editor commit flow only.
- Q: Where is `version_name` displayed and edited in the Versions panel? → A: Standalone editable text field above the entries table; editable for WIP only, read-only for released versions.
- Q: What should happen when a user attempts to release a version and a released version file with the same `version_name` already exists? → A: Block the release with a clear error: "Version X already exists. Please change the WIP version name."
- Q: What should happen when releasing a product whose `wip.json` has no entries? → A: Block the release with an error: "Cannot release a version with no change entries."
- Q: How should the Versions panel behave when `wip.json` is malformed or has an unexpected structure? → A: Show an error state with a "Reset to empty WIP" button that creates a fresh valid `wip.json`; do not silently auto-repair.
- Q: What characters are permitted in `version_name` (used as filename and git tag)? → A: Alphanumeric, dots, hyphens, and underscores only (e.g., `1.0.0`, `v1-beta_rc`).
- Q: When multiple semicolon-separated authors are provided and one or more are invalid, how should validation respond? → A: Reject the entire author field and list each invalid author (e.g., "Invalid authors: 'JohnDoe', 'Jane'").

## Assumptions

- The "product short name" used for git tags is the same identifier already used as the product's directory name in `infra/`.
- The release workflow already exists (PDF generation, git commit); this feature extends it with versioning data — it does not replace the existing release mechanism.
- The web editor already has a product tree sidebar; the "Versions" entry is added as a new node within that existing tree structure.
- Date values in version entries are stored as ISO 8601 date strings (YYYY-MM-DD); the UI provides a date picker.
- The Versions panel shows all versions (WIP and released) via a version selector; released versions are in scope for this feature as read-only views.
- The commit-time version note prompt is presented within the web editor's existing commit flow, not as a standalone git hook outside the editor.

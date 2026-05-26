# Product Versioning — Overview

## Feature Description

Product versioning lets you track a structured change history for each product defined in `infra/`. Each product maintains a **work-in-progress (WIP) version file** (`infra/<shortname>/versioning/wip.json`) that accumulates change entries until you perform a **release**. On release, the WIP file is promoted to an immutable named version file, a version history table is injected into the rendered AsciiDoc document, a git tag is created, and a new WIP file is seeded for the next release.

## Release Workflow

```
[WIP entries accumulate over time]
        |
        v
User clicks "Release" in Product panel
        |
        v
Enter new WIP version name (e.g. "1.1.0")
        |
        v
Backend validates:
  - wip.json is not empty (at least one entry)
  - version_name is set and valid
  - no duplicate version file already exists
        |
        v
  [1] Write infra/<sn>/versioning/<version>.json  (immutable)
  [2] Regenerate output/<sn>.adoc with Version History table
  [3] Attempt PDF build (best-effort; skipped if asciidoctor-pdf absent)
  [4] Seed new infra/<sn>/versioning/wip.json
      (version_name = new version name, one entry seeded from last released entry)
  [5] git add -A && git commit
  [6] git tag <sn>-<version>
        |
        v
Response: { version_name, tag, commit_sha, pdf_generated, new_wip_version_name }
```

## Operations Guide

### Adding the first version entry

1. Open the web editor and expand the product in the tree.
2. Click the "Versions" leaf node — this opens the Versioning panel.
3. In the "Version Name" field, enter a version identifier (e.g. `1.0.0`).
4. Click "+ Add Entry" and fill in Author (format: `Surname, Firstname`), Date, and optional Notes.
5. The entry is immediately persisted to `infra/<shortname>/versioning/wip.json`.

### Releasing a version

1. Navigate to the product node in the tree and click it to open the Product panel.
2. Click the **"Release…"** button (only visible for products that are not in ADDED state).
3. In the release dialog, enter the **new WIP version name** (the name for the *next* WIP cycle, e.g. `1.1.0`).
4. Click **"Confirm Release"**. The dialog shows the released tag and whether PDF was generated.
5. Click **"Close"** — the tree and versioning panel refresh automatically.

### Recovering from a malformed wip.json

If `wip.json` is corrupted or unparseable, the Versioning panel shows an error banner with a **"Reset to empty WIP"** button. Clicking it replaces the file with a fresh empty structure (version_name `""`, no entries) and loads the clean state.

### Adding a version note at commit time

1. Open the Commit panel (top-right button in the editor).
2. If any product has pending changes, a collapsible "Add version note for \<shortname\>" section appears.
3. Expand the section, fill in Author and Date, and optionally add Notes.
4. Click **"Commit & Push"** — the note is appended to `infra/<shortname>/versioning/wip.json` as part of the commit.
5. Leaving the section collapsed skips the note entirely — the commit proceeds normally.

## Author Format

Author fields use `Surname, Firstname` format. Multiple authors are separated by semicolons:

```
Smith, John
Smith, John; Doe, Jane
```

Invalid tokens are rejected individually — the error message lists each failing token.

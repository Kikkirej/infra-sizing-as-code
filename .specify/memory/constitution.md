<!--
  Sync Impact Report
  ==================
  Version change: unversioned (template) → 1.0.0

  Added Sections:
  - Core Principles I–V: Git as Truth, File-First Architecture,
    Infrastructure as Code, CI/CD Portability, Documentation-Driven
  - Project Structure: canonical directory layout (src/, infra/, docs/)
  - Build Requirements: GitLab CI + GitHub Actions dual-platform mandate
  - Governance: amendment procedure, versioning policy, compliance gate

  Modified Principles: N/A — initial constitution fill
  Removed Sections: N/A — initial constitution fill

  Templates reviewed:
  - .specify/templates/plan-template.md     ✅ updated (structure options aligned
    to src/ / infra/ / docs/ layout)
  - .specify/templates/spec-template.md     ✅ reviewed — no changes required
  - .specify/templates/tasks-template.md    ✅ updated (path conventions extended
    with infra/ and docs/)
  - .specify/templates/constitution-template.md  ✅ reviewed — source template;
    no update needed

  Deferred TODOs:
  - None. RATIFICATION_DATE set to 2026-05-24 (initial ratification, no prior
    record found).
-->

# Infra Sizing as Code Constitution

## Core Principles

### I. Git as Single Source of Truth

All state MUST be persisted in Git. No external databases or ephemeral state
stores are permitted. Every artifact — configuration, sizing data, decisions —
MUST exist as a file under version control. The Git history IS the audit log;
side-channel state is prohibited.

### II. File-First Architecture

The repository MUST follow the canonical three-folder structure:

- `src/` — all application logic and business rules
- `infra/` — all infrastructure definitions (declarative, reproducible)
- `docs/` — all feature documentation and file-structure references

Files MUST be placed in the correct folder without exception. Cross-folder
dependencies MUST flow in one direction: `infra/` may reference `src/` outputs;
`docs/` documents both. No code in `docs/`, no documentation prose in `src/`.

### III. Infrastructure as Code

All infrastructure MUST be defined declaratively in `infra/`. Manual provisioning
is prohibited. Every resource definition MUST be version-controlled,
peer-reviewed, and fully reproducible from the files alone. Infrastructure
changes MUST go through the same Git review workflow as application changes.

### IV. CI/CD Portability

Build pipelines MUST be implemented for both GitLab CI (`.gitlab-ci.yml`) and
GitHub Actions (`.github/workflows/`). Pipeline logic MUST be portable: shared
steps MUST be extracted into scripts (in `src/` or a dedicated `scripts/`
directory) so neither platform receives privileged logic that the other lacks.
Both pipeline definitions MUST remain in sync and MUST pass before any branch
is merged.

### V. Documentation-Driven Development

Every feature MUST have corresponding documentation in `docs/` before it is
considered complete. Documentation MUST describe the feature's purpose, the
file structures it introduces or modifies, and any operational runbook steps.
Undocumented features MUST NOT be merged to main.

## Project Structure

The canonical directory layout for this repository:

```text
src/      # Application logic and business rules
infra/    # Infrastructure definitions (declarative, reproducible)
docs/     # Feature documentation and file-structure references
```

All new files MUST be placed in the appropriate top-level folder. Additional
subdirectories within each folder are permitted but MUST follow conventions
documented in `docs/`.

## Build Requirements

Both CI/CD platforms MUST be supported at all times:

- **GitLab CI**: pipeline defined in `.gitlab-ci.yml` at repository root
- **GitHub Actions**: pipelines defined under `.github/workflows/`

Pipeline parity is MANDATORY. Any build step available on one platform MUST
have a functional equivalent on the other. Shared logic MUST be extracted into
scripts to avoid duplication. Both pipeline definitions MUST be updated together
as part of any feature branch before merge.

## Governance

This constitution supersedes all other development practices and agreements.
Amendments MUST be proposed via pull/merge request, include a rationale, and
update this document's version and `Last Amended` date before merging.

**Versioning policy**:
- MAJOR: removal or incompatible redefinition of an existing principle
- MINOR: new principle or section added, or materially expanded guidance
- PATCH: clarifications, wording fixes, non-semantic refinements

All pull/merge requests MUST include a Constitution Check: reviewers MUST
verify that proposed changes comply with all five core principles before
approving. Complexity deviations MUST be justified in the plan's Complexity
Tracking table.

**Version**: 1.0.0 | **Ratified**: 2026-05-24 | **Last Amended**: 2026-05-24

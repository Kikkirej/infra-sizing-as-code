# Feature Specification: Infrastructure Sizing Document Export

**Feature Branch**: `001-infra-sizing-doc-export`

**Created**: 2026-05-24

**Status**: Draft

**Input**: User description: "Defining an infrastructure and exporting it to a document. Build flow is 1. Generate asciidoc, 2. Build PDFs with fitting includes 3. archive documents."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define Infrastructure Hierarchy and Generate Document (Priority: P1)

A technical author or infrastructure engineer defines a product with one or more
sizing tiers. Each tier describes the required server flavours and hardware
specifications. They trigger the build and receive a PDF document that accurately
reflects the defined infrastructure.

**Why this priority**: This is the core end-to-end value of the system. Without
a complete definition-to-document pipeline, no other capability has meaning.

**Independent Test**: Can be fully tested by creating a minimal product definition
(one product, one size, one flavour, one server) and running the full build; the
result is a readable PDF containing the correct hardware data.

**Acceptance Scenarios**:

1. **Given** a product definition with one size and one flavour containing at least one server,
   **When** the build is triggered,
   **Then** a PDF is produced containing an AsciiDoc table with the server's
   system, count, CPU, CPU clocking, memory, disk partitions, network, software,
   and comment columns.

2. **Given** a product with exactly one size defined,
   **When** the PDF is generated,
   **Then** the size tier heading is omitted from the document (single-size suppression).

3. **Given** a product with multiple sizes,
   **When** the PDF is generated,
   **Then** each size is shown as a distinct section with its own prefix text, infrastructure tables, and suffix text.

4. **Given** a server definition whose disk contains multiple partitions,
   **When** the PDF is generated,
   **Then** each partition is listed individually within the server's disk section.

---

### User Story 2 - Multi-Product Build with Per-Product Documents (Priority: P2)

Multiple products are defined in the repository. The build produces one PDF per
product, each composed of the correct combination of shared and product-specific
content sections.

**Why this priority**: The multi-product capability is the primary scaling
mechanism; a single-product build is the degenerate case and is covered by US1.

**Independent Test**: Define two products; trigger build; verify two distinct PDFs
are produced, each containing the correct product-specific preamble and suffix
sections while sharing the common preamble and suffix.

**Acceptance Scenarios**:

1. **Given** N products are defined,
   **When** the build runs,
   **Then** exactly N PDFs are produced, one per product.

2. **Given** a product PDF,
   **When** inspecting its structure,
   **Then** sections appear in the mandated order:
   generated deck/TOC → common preamble → product-specific preamble →
   infrastructure content → product-specific suffix → common suffix.

3. **Given** a change to the common preamble text,
   **When** the build runs,
   **Then** the updated preamble appears in every product's PDF.

---

### User Story 3 - Archive Build Artefacts (Priority: P3)

After PDFs are generated, the build archives all output documents so they can
be distributed or stored as a versioned release artefact.

**Why this priority**: Archiving is a post-processing step that does not affect
document correctness; it is required for distribution but does not block US1/US2.

**Independent Test**: Trigger a full build for at least one product; verify an
archive file is produced containing all generated PDFs.

**Acceptance Scenarios**:

1. **Given** a successful PDF generation step,
   **When** the archive step runs,
   **Then** a ZIP file is created containing all generated PDFs.

2. **Given** one or more products fail during PDF generation,
   **When** the archive step runs,
   **Then** all successfully generated PDFs are archived, all errors are reported
   together, and the build exits with a failure code.

---

### Edge Cases

- **Product with no sizes / size with no flavours / flavour with no servers**: Fail
  hard for that product with a clear validation error; continue processing remaining
  products (FR-008a).
- How does the system handle a server with no disk partitions?
- **Missing product-specific preamble or suffix file**: Fail hard for that product
  with a clear error; continue remaining products (FR-008a).
- **Missing `theme.yml`**: Fail the entire build immediately with a clear error
  before processing any product.
- What happens if `infra/products.json` is missing or malformed?
- What happens if a product listed in `products.json` has no corresponding folder under `infra/`?
- What happens if a shortname in `products.json` does not match any folder name?
- How does the build behave when only one product is defined (single-product build)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support a three-level infrastructure hierarchy:
  Product → Size → Flavour → Server.
- **FR-002**: N products MUST be supported; each product triggers its own PDF
  output during a build.
- **FR-003**: A product MUST have 1 to N sizes; a size MUST have 1 to N flavours;
  a flavour MUST have 1 to N servers.
- **FR-004**: When exactly one size is defined for a product, the size heading and
  tier information MUST NOT appear in the generated document.
- **FR-005**: Each size MUST support an optional prefix text and an optional suffix
  text that wrap its infrastructure content in the PDF.
- **FR-006**: Server definitions MUST include the following fields, rendered as
  columns in an AsciiDoc table in the order listed:
  **system** (free-text, describes the server's purpose; first column),
  **count** (positive integer, number of instances; defaults to 1),
  **cpu** (free-text, e.g. "4 vCPU"),
  **cpu_clocking** (free-text clock speed, e.g. "3.2 GHz"; placed after CPU),
  **memory** (free-text, e.g. "32 GB"),
  **disk** (list of partitions, each with size, performance, and optional comment),
  **network** (optional free-text list, e.g. ["2× 10GbE", "1× 1GbE"]),
  **software** (optional free-text list, e.g. ["Oracle DB 19c", "NGINX"]),
  **comment** (optional free-text).
- **FR-006a**: The `network` and `software` fields are optional lists of free-text
  strings. When present and non-empty, items MUST be displayed as a bulleted or
  newline-separated list within the table cell. When absent or empty, the cell
  MUST render blank.
- **FR-007**: Disk MUST be represented as a list of partitions; each partition is
  listed individually within the Disk cell of the server table. A partition MUST
  contain three fields: **size** (storage capacity, e.g. "500 GB"),
  **performance** (free-text storage tier, e.g. "NVMe SSD", "7200 RPM HDD"),
  and **comment** (optional free-text description).
- **FR-007a**: Within a flavour, all servers MUST be rendered as a single AsciiDoc
  table. Each server occupies one row. Column order MUST follow FR-006: System,
  Count, CPU, CPU Clocking, Memory, Disk, Network, Software, Comment.
- **FR-008**: The build MUST execute in three ordered steps:
  (1) generate AsciiDoc source, (2) build PDFs from AsciiDoc, (3) archive PDFs.
  The entry point MUST be a single `build.py` script that runs all three stages
  sequentially via discrete internal stage functions.
- **FR-008a**: If one or more products fail during step (1) or (2) — including
  validation failures such as a product having no sizes, a size having no
  flavours, or a flavour having no servers — the build MUST continue processing
  all remaining products, collect all errors, report them together at the end,
  and exit with a non-zero failure code. Successfully generated PDFs from that
  run MUST still be available.
- **FR-009**: Each PDF MUST be composed of the following sections in order:
  (1) generated cover page (document title, product name, build date/version) and
  auto-generated TOC, (2) common preamble, (3) product-specific preamble,
  (4) all infrastructure content for that product, (5) product-specific suffix,
  (6) common suffix.
- **FR-010**: Common preamble and common suffix MUST be identical across all
  product PDFs.
- **FR-011**: Product-specific preamble and product-specific suffix MUST be unique
  per product.
- **FR-012**: All infrastructure definitions MUST be stored in a hierarchical
  directory tree under version control (no external database). The canonical
  layout is: `infra/products.json`; `infra/{p}/sizes.json`; `infra/{p}/meta.json`;
  `infra/{p}/{s}/flavours.json`; `infra/{p}/{s}/meta.json`;
  `infra/{p}/{s}/{f}/meta.json`; `infra/{p}/{s}/{f}/servers.json`; where `{p}`,
  `{s}`, `{f}` are shortnames (no numeric prefix on any folder).
- **FR-013**: Display names are stored exclusively in registry files (FR-016) and
  MUST NOT be duplicated in `meta.json`. Each `meta.json` at the product level
  MUST contain the relative paths to the product-specific preamble and suffix
  files. Each `meta.json` at the size level MUST contain the prefix text and
  suffix text.
- **FR-013a**: The common preamble and common suffix MUST be stored as AsciiDoc
  files directly under `infra/` (`infra/preamble.adoc`, `infra/suffix.adoc`).
  Product-specific preamble and suffix files MUST also be AsciiDoc (`.adoc`).
  All preamble/suffix files are included verbatim into the generated AsciiDoc
  document before PDF conversion. The build MUST locate common files at their
  fixed paths and product-specific files via paths in the product's `meta.json`.
- **FR-014**: Each flavour MUST be a directory named `{shortname}/` within the
  size directory (no numeric prefix). The flavour directory MUST contain a
  `meta.json` (optional image entry only; display name is in the parent
  `flavours.json`) and a `servers.json` (server definitions). Display order is
  controlled by `flavours.json`, not by directory naming.
- **FR-017**: Each flavour directory MAY contain an optional `preamble.adoc` and
  an optional `suffix.adoc` (AsciiDoc). When present, these are included in the
  PDF before and after the flavour's server table respectively.
- **FR-018**: A flavour's `meta.json` MAY include an optional image entry with a
  `type` and a `value`. `type: file` — `value` is a relative path to an image
  file (rendered inline in the PDF). `type: mermaid` — `value` is a relative path
  to a `.mmd` file within the flavour folder; rendered via the `asciidoctor-diagram`
  plugin and local `mermaid-cli` (`mmdc`) without external network access. When
  the image entry is absent, no image is included for that flavour.
- **FR-015**: A `theme.yml` file at the repository root MUST be used to control
  the visual styling (fonts, colours, layout) of all generated PDFs. All product
  PDFs MUST use the same theme file. If `theme.yml` is absent, the build MUST
  fail immediately before processing any product.
- **FR-015a**: If a product-specific preamble or suffix file path is listed in a
  product's `meta.json` but the file does not exist on disk, the build MUST fail
  that product with a clear error and continue processing remaining products
  (consistent with FR-008a).
- **FR-016**: Registry files at each hierarchy level MUST control both discovery
  and display order. `infra/products.json` lists all products; each product folder
  contains `sizes.json` listing that product's sizes; each size folder contains
  `flavours.json` listing that size's flavours. Every registry entry MUST include
  at minimum a shortname and a display name. The build MUST process each level
  exclusively in the order declared by its registry file.
- **FR-019**: Each product folder MUST contain a `sizes.json` listing the product's
  sizes in display order. The build MUST NOT infer size ordering from directory
  names or filesystem sort order.
- **FR-020**: Each size folder MUST contain a `flavours.json` listing the size's
  flavours in display order. The build MUST NOT infer flavour ordering from
  directory names or filesystem sort order.
- **FR-021**: A `README.md` at the repository root MUST provide a `docker run`
  command for local builds that mounts the repository working directory and
  invokes `build.py` inside a container with all required toolchain dependencies
  (asciidoctor-pdf, asciidoctor-diagram, mermaid-cli) pre-installed.

### Key Entities

- **Product**: Top-level grouping that maps to one output PDF. Has a **shortname**
  (folder name under `infra/`) and a **display name** (stored exclusively in
  `infra/products.json`). The product folder contains a `meta.json` (holding
  preamble/suffix file paths only) and one sub-directory per size.
- **Size**: A named tier within a product (e.g., "50 users", "500 users"). Has a
  **shortname** (folder name) and a **display name** (stored exclusively in the
  parent product's `sizes.json`). Its `meta.json` contains only the prefix text
  and suffix text for that size. Contains one or more flavour sub-directories.
- **Flavour**: A named server-role grouping within a size; stored as a directory
  `{shortname}/` (no numeric prefix). Has a **shortname** (directory name) and a
  **display name** (stored exclusively in the parent size's `flavours.json`).
  Display order is controlled by the parent size's `flavours.json`. Contains
  `meta.json` (optional image entry only), optional `preamble.adoc`, optional
  `suffix.adoc`, and `servers.json`. May include an optional image entry (type
  `file` or `mermaid`) in `meta.json`.
- **Server**: A concrete hardware specification rendered as a row in an AsciiDoc
  table. Fields in column order: **system** (purpose description), **count**
  (positive integer, defaults to 1), **cpu** (free-text), **cpu_clocking**
  (free-text clock speed), **memory** (free-text), **disk** (list of partitions),
  **network** (free-text list of interfaces), **software** (free-text list of
  components), **comment** (optional free-text).
- **Partition**: A single disk partition entry within a server definition. Has three
  fields: **size** (storage capacity, e.g. "500 GB"), **performance** (free-text
  storage tier, e.g. "NVMe SSD", "7200 RPM HDD"), and **comment** (optional
  free-text label or description).
- **Common Preamble / Common Suffix**: Shared document sections applied to every
  product PDF unchanged; stored as `infra/preamble.adoc` and `infra/suffix.adoc`.
- **Product Preamble / Product Suffix**: Per-product document sections stored
  within the product folder (e.g., `infra/{shortname}/preamble.adoc`); paths
  referenced from the product's `meta.json`.
- **Flavour Image**: An optional entry in a flavour's `meta.json` specifying a
  diagram or image to render in the PDF. Has a `type` (`file` — relative path to
  an image file; `mermaid` — relative path to a `.mmd` file in the flavour folder)
  and a `value` (the path). Omitted entries produce no image in the output.
- **Product Registry** (`infra/products.json`): Lists all products with shortname
  and display name, in display order. The build discovers and orders products
  exclusively from this file.
- **Size Registry** (`infra/{p}/sizes.json`): Lists all sizes for a product with
  shortname and display name, in display order. Controls size ordering in the PDF.
- **Flavour Registry** (`infra/{p}/{s}/flavours.json`): Lists all flavours for a
  size with shortname and display name, in display order. Controls flavour ordering
  in the PDF.
- **Theme**: A single `theme.yml` file at the repository root defining visual
  styling (fonts, colours, layout) applied uniformly to all generated PDFs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A complete build for 5 products with 3 sizes each completes without
  manual intervention.
- **SC-002**: The generated PDF structure matches the mandated section order
  (FR-009) for every product, verifiable by document inspection.
- **SC-003**: Single-size products produce PDFs with no size-tier headings,
  verifiable by reviewing the rendered output.
- **SC-004**: All server data (system, count, CPU, CPU clocking, memory, disk
  partitions, network entries, software entries, comment) present in a definition
  appears correctly as columns in the corresponding AsciiDoc table in the PDF.
- **SC-005**: A single ZIP archive (`.zip`) containing all generated product PDFs
  is produced at the end of every build (including partial-failure builds where
  at least one PDF was successfully generated).
- **SC-006**: Infrastructure definitions can be added, modified, or removed via
  Git without requiring changes to the build tooling itself.

## Clarifications

### Session 2026-05-24

- Q: What file format should infrastructure definitions use? → A: JSON — one `.json` file per product under `infra/`
- Q: How are infrastructure definitions organised on disk? → A: Hierarchical directory tree — one folder per product, one sub-folder per size; each level has a `meta.json` for its metadata. Each size folder contains multiple numbered flavour files named `NNN-flavourshortname.json` (e.g. `001-appserver.json`, `002-dbserver.json`). *(Corrected: earlier answer incorrectly stated a single `{size}.json` per size.)*
- Q: How are flavour files named and ordered within a size? → A: Sequential numeric prefix + short name: `001-flavourshortname.json`. The prefix controls display order in the generated document.
- Q: Where is the PDF theme/styling defined? → A: A `theme.yml` file at the repository root applies to all generated PDFs.
- Q: What does the "deck" section of the PDF contain? → A: A generated cover page containing the document title, product name, and build date/version.
- Q: How should the build behave when one product fails? → A: Continue processing all products, collect all errors, report them together at the end, and exit with a failure code.
- Q: What format should the build archive use? → A: ZIP (`.zip`) — a single archive containing all generated product PDFs.
- Q: Do entities have both a short name and a display name? → A: Yes — every Product, Size, and Flavour has a shortname (used for file/folder names) and a display name (used in the PDF). *(Corrected: display names are stored exclusively in the registry files — `products.json`, `sizes.json`, `flavours.json` — not in `meta.json`. See final clarification below.)*
- Q: How are all products registered / discovered by the build? → A: A top-level `infra/products.json` file lists all products with their shortname and display name. The build uses this as its authoritative product registry.
- Q: What fields does a disk partition contain? → A: Size and comment. No mount point or filesystem type.
- Q: What format are CPU and memory server fields? → A: Free-text strings for both (e.g., CPU: "4 vCPU", Memory: "32 GB"). No enforced structure.
- Q: Where do preamble and suffix content files live in the repository? → A: Under `infra/` — common preamble/suffix at the `infra/` root; product-specific preamble/suffix alongside the product folder (path referenced from `meta.json`).
- Q: Does a server have a name or label? → A: Yes — a free-text display name shown as a label in the PDF.
- Q: Does a server definition include a quantity? → A: Yes — an integer `count` field (e.g., `count: 3` = "3 servers of this spec"); default is 1.
- Q: What format are preamble and suffix files? → A: AsciiDoc (`.adoc`) — included directly into the generated AsciiDoc document before PDF conversion.
- Q: Does a flavour follow the same folder hierarchy pattern as products and sizes? → A: Yes — each flavour is a folder (`NNN-{shortname}/`) containing `meta.json`, optional `preamble.adoc`, optional `suffix.adoc`, and `servers.json` for server definitions.
- Q: Does each flavour support an optional diagram or image? → A: Yes — `meta.json` may include an optional image entry with `type: file` (path to an image file) or `type: mermaid` (mermaid diagram). If absent, no image is rendered.
- Q: How is ordering controlled for sizes and flavours? → A: Registry files control ordering: `sizes.json` inside each product folder lists sizes in display order; `flavours.json` inside each size folder lists flavours in display order. The `NNN-` numeric prefix is dropped from flavour folder names — folders are named with the shortname only.
- Q: Is there a registry file pattern at every hierarchy level? → A: Yes — `products.json` (infra root), `sizes.json` (product folder), `flavours.json` (size folder). Each registry lists entries in the desired display order with their shortname and display name.
- Q: For a flavour image of type `mermaid`, is the diagram inline or a file reference? → A: File reference — `value` is a relative path to a `.mmd` file within the flavour folder.
- Q: What is the complete server field set and table column order? → A: System (purpose description, first column; replaces "name"), Count, CPU, CPU Clocking (clock speed, after CPU), Memory, Disk (list of partitions), Network (free-text list), Software (free-text list), Comment (optional). Servers are rendered as an AsciiDoc table in the generated document.
- Q: What fields does a disk partition have? → A: Three fields — size, performance (free-text, e.g. "NVMe SSD", "7200 RPM HDD"), and comment (optional). *(Extends prior answer of size + comment.)*
- Q: Are `network` and `software` server fields required or optional? → A: Both optional — omitting the field or providing an empty list renders an empty cell in the AsciiDoc table.
- Q: Which is authoritative for display names — registry files or `meta.json`? → A: Registry files are authoritative. Display names are stored only in the registry (products.json, sizes.json, flavours.json). `meta.json` files drop the display name and contain only their level-specific metadata.
- Q: What language/runtime should the build scripts use? → A: Python 3 (stdlib-only) — no external dependencies beyond the AsciiDoc/Mermaid toolchain.
- Q: What should the build do when a product has no sizes, a size has no flavours, or a flavour has no servers? → A: Fail hard for that product with a clear validation error message; continue processing all remaining products (consistent with FR-008a).
- Q: How should Mermaid diagrams be rendered into PDFs? → A: asciidoctor-diagram plugin + local mermaid-cli (`mmdc`) — offline, no external network dependency.
- Q: What should the build do when an explicitly referenced file is missing (product preamble/suffix, `theme.yml`)? → A: Missing product-specific preamble or suffix fails that product (errors collected per FR-008a); missing `theme.yml` fails the entire build immediately.
- Q: Should the build be a single entry-point script or separate per-stage scripts? → A: Single `build.py` entry point running all three stages sequentially via discrete internal functions. A `README.md` MUST include a `docker run` command for local builds.

## Assumptions

- Infrastructure definitions are stored as JSON files in this canonical layout:
  ```
  infra/
  ├── products.json                   ← product registry (ordered shortname + display name)
  ├── preamble.adoc                   ← common preamble (all products)
  ├── suffix.adoc                     ← common suffix (all products)
  └── {product-shortname}/
      ├── meta.json                   ← preamble/suffix file paths (no display name)
      ├── sizes.json                  ← size registry (ordered shortname + display name)
      ├── preamble.adoc               ← product-specific preamble
      ├── suffix.adoc                 ← product-specific suffix
      └── {size-shortname}/
          ├── meta.json               ← prefix/suffix text only (no display name)
          ├── flavours.json           ← flavour registry (ordered shortname + display name)
          └── {flavour-shortname}/    ← no NNN- prefix; order from flavours.json
              ├── meta.json           ← optional image entry only (no display name)
              ├── preamble.adoc       ← optional flavour preamble
              ├── suffix.adoc         ← optional flavour suffix
              └── servers.json        ← server definitions for this flavour
  ```
  Every entity (Product, Size, Flavour) has a shortname (file/folder identity)
  and a display name (PDF presentation). No GUI authoring tool is required.
- A `theme.yml` file at the repository root defines the visual styling applied
  to all generated PDFs. Its presence is required for a successful build.
- The AsciiDoc-to-PDF toolchain (`asciidoctor-pdf`) with the `asciidoctor-diagram`
  plugin and local `mermaid-cli` (`mmdc`) is available in the build environment;
  toolchain installation is out of scope for this feature. Mermaid diagrams are
  rendered offline via `mmdc` — no external network access is required.
- All preamble and suffix files are AsciiDoc (`.adoc`) and included verbatim
  into the generated AsciiDoc document before PDF conversion. Common files are
  at `infra/preamble.adoc` and `infra/suffix.adoc`. Product-specific files are
  stored within the product's folder and their paths are referenced from `meta.json`.
- Both GitLab CI and GitHub Actions pipeline definitions must support the full
  three-step build as per the project constitution.
- The deck section of each PDF is a generated cover page containing the document
  title, product name, and build date/version; the TOC is generated automatically
  from the document structure. No manual authoring is required for either.
- A "build" is triggered via the CI/CD pipeline or a local script; interactive
  GUI builds are out of scope.
- Build scripts are implemented in Python 3 using the standard library only
  (json, pathlib, subprocess, zipfile). No third-party Python packages are
  required beyond the AsciiDoc/Mermaid toolchain binaries.
- A `README.md` at the repository root MUST document how to run the build
  locally, including a `docker run` command that mounts the repository and
  executes `build.py` inside a container that has all required toolchain
  dependencies pre-installed (asciidoctor-pdf, asciidoctor-diagram, mermaid-cli).

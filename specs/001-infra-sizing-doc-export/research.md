# Research: Infrastructure Sizing Document Export

**Phase 0 output** | **Branch**: `001-infra-sizing-doc-export` | **Date**: 2026-05-24

## 1. AsciiDoc Generation Strategy

**Decision**: Python generates `.adoc` files programmatically using f-strings and
string concatenation. All `include::` directives use paths relative to the repo
root; `asciidoctor-pdf` is invoked with `-B {repo_root}` so the base directory
for include resolution is always the repo root regardless of where the `.adoc`
file lives.

**Rationale**: No external templating library needed (stdlib-only constraint).
Relative-to-root include paths are stable even when the generated `.adoc` files
are placed in `output/`. The `-B` flag is the canonical asciidoctor mechanism
for this pattern.

**Alternatives considered**:
- Jinja2 templating — rejected (external dependency).
- Generating `.adoc` at repo root alongside `infra/` — rejected (pollutes root;
  `output/` is the correct artifact directory).
- Copying all source files into `output/` and using local relative paths —
  rejected (unnecessary file churn; asciidoctor-pdf `-B` solves this cleanly).

---

## 2. asciidoctor-pdf Invocation

**Decision**: Invoke via `subprocess.run` with the following arguments:

```
asciidoctor-pdf
  -r asciidoctor-diagram          # load diagram extension
  -a pdf-theme={theme_filename}   # theme file name (stem only)
  -a pdf-themesdir={repo_root}    # directory containing theme.yml
  -B {repo_root}                  # base dir for include:: resolution
  -D {output_dir}                 # destination directory for PDF
  {adoc_path}                     # input .adoc file
```

Capture `stdout` and `stderr` with `capture_output=True, text=True`.
Non-zero return code is treated as a product-level failure (FR-008a).

**Rationale**: `-r asciidoctor-diagram` activates mermaid/diagram support inline.
`-a pdf-themesdir` separates theme directory from theme name as required by
asciidoctor-pdf. `-B` ensures all `include::` paths in the generated document
resolve relative to the repo root.

**Alternatives considered**:
- Pre-rendering mermaid via direct `mmdc` subprocess calls from Python then
  using `image::` — rejected (asciidoctor-diagram handles this automatically;
  adds unnecessary complexity and an extra subprocess dependency in Python code).

---

## 3. Generated AsciiDoc Document Structure

**Decision**: Each product's `.adoc` has the following structure:

```asciidoc
= {product_display_name}
:doctype: book
:toc:
:title-page:
:revdate: {YYYY-MM-DD}
:nofooter:

include::infra/prefix.adoc[]

include::infra/{product_shortname}/prefix.adoc[]

// — repeated per size (omit == heading if exactly one size: FR-004) —
== {size_display_name}

{size_prefix_text}

// — repeated per flavour —
=== {flavour_display_name}

// Optional image (type: file)
image::infra/{product}/{size}/{flavour}/{value}[]

// Optional image (type: mermaid) — mmd content embedded for asciidoctor-diagram
[mermaid,{product}-{size}-{flavour}-diagram,png]
----
{content of .mmd file}
----

// Optional flavour prefix
include::infra/{product}/{size}/{flavour}/prefix.adoc[]

// Server table — 5 columns; no separate Count/Network/Software columns
[cols="15,14,13,43,33",options="header"]
|===
| System | CPU | Memory | Disk | Comment

| {system_cell} | {cpu.render()} ({cpu_clocking}) | {memory.render()}
a| {disk_cells}
a| {comment_cell}

|===

// Optional flavour suffix
include::infra/{product}/{size}/{flavour}/suffix.adoc[]

{size_suffix_text}
// — end per size —

include::infra/{product_shortname}/suffix.adoc[]

include::infra/suffix.adoc[]
```

**Server table column layout**:
- Always 5 columns: **System** | **CPU** | **Memory** | **Disk** | **Comment**
- No separate Count, Network, or Software columns

**System cell format**:
- `count == 1`: `{system}` (no annotation)
- `count > 1`: `{system} [{count}]` — e.g. `Application Server [3]`

**Comment cell format**: Combines network items, software items, and the original
comment string into a single `a|` cell. Build order:
1. Software items (if any) — each as `* {item}` bullet
2. Network items (if any) — each as `* {item}` bullet
3. Original comment text (if non-empty) — appended after bullets

Combined example:
```asciidoc
a|
* OpenJDK 17
* NGINX 1.25
* 2× 10GbE

Active/active pair
```

When all three are empty/absent: blank `a|` cell.
When only comment text (no network/software): plain text in `a|` cell.

**Disk cell format — primary (nested table)**: Use AsciiDoc `!===` nested table
inside the `a|` Disk cell. The `!` delimiter is the AsciiDoc convention for nested
table rows/cells and is supported by asciidoctor-pdf.

```asciidoc
a|
[cols="3,3,3",options="header"]
!===
! Size ! Perform- +
ance ! Comment/ +
Usage
! 100 GB ! NVMe SSD ! OS
! 500 GB ! NVMe SSD ! App data
!===
```

For a partition with no comment, the Comment cell is left blank:
```asciidoc
! 2 TB ! 7200 RPM HDD !
```

For a dynamic partition size:
```asciidoc
! n × 500 GB ! NVMe SSD ! Data (per node)
```

**Disk cell format — fallback (if nested table renders poorly in asciidoctor-pdf)**:
Show a total storage summary in the main table cell and emit a separate partition
detail table after the server table, one per server (labelled by system name).

*Main cell (fallback)*: `{total_storage} ({n} partitions)`
- Total storage computed by summing static TypedValues in GB, then auto-scaling:
  if ≥ 1000 GB → display in TB. If any partition is dynamic: append `+ variable`.
- Examples: `1.6 TB (3 partitions)`, `100 GB + variable (2 partitions)`
- All dynamic: `variable (2 partitions)`

*Separate partition table (fallback)*, emitted after each server table:
```asciidoc
.Partitions — {system_name}
[cols="3,3,3",options="header"]
|===
| Size | Performance | Comment
| 100 GB | NVMe SSD | OS
| 500 GB | NVMe SSD | App data
|===
```

When a flavour has multiple servers, each server gets its own titled partition table.

**Single-size suppression (FR-004)**: When `len(sizes) == 1`, omit the
`== {size_display_name}` heading. Prefix/suffix text and all content still render.

**CPU column format** (merged CPU + CPU Clocking): The CPU and CPU Clocking
fields are always rendered as a single column in the header and each row.
Format: `{cpu.render()} ({cpu_clocking})` → e.g. `8 vCPU (3.2 GHz)` or
`n × 4 vCPU (3.0 GHz)`. Column header: `CPU`.

**Rationale**: Merging Count into the System name and folding Network/Software
into Comment reduces the table from 7–8 columns to 5. Narrower tables fit better
on A4 landscape and avoid line-wrapping in the Disk column. Count is still visible
(as `[N]` suffix) for the reader; Network and Software remain queryable in the
source JSON but are secondary information in the rendered view.
AsciiDoc `!===` nested tables are supported in asciidoctor-pdf and give the
cleanest tabular structure for partitions.

---

## 4. Mermaid Diagram Rendering

**Decision**: For `image.type: mermaid` in a flavour's `meta.json`:
1. Read the `.mmd` file content from the path in `image.value` (relative to the
   flavour directory).
2. Embed the content in the generated `.adoc` as an asciidoctor-diagram mermaid
   block with a unique diagram name:
   ```asciidoc
   [mermaid,{product}-{size}-{flavour}-diagram,png]
   ----
   {mmd_content}
   ----
   ```
3. asciidoctor-diagram invokes `mmdc` automatically at PDF build time.
   No network access required (FR-018).

For `image.type: file`: emit `image::infra/{rel_path}[]` where `rel_path` is
relative to repo root.

**Rationale**: Embedding mermaid content (not a file include) avoids the
`include::` path complexity for sub-path files. The unique diagram name prevents
cache collisions when multiple flavours have diagrams.

**Alternatives considered**:
- `include::` for `.mmd` file inside a mermaid block — works but requires
  asciidoctor-diagram to support include within a block, which is fragile.
- Pre-render PNG via `mmdc` subprocess in Python — rejected (moves rendering
  responsibility out of asciidoctor-diagram; breaks the single-tool chain).

---

## 5. Output Directory Layout

**Decision**: `output/` at repo root, gitignored.

```
output/
├── {product-shortname}.adoc     # generated per Stage 1
├── {product-shortname}.pdf      # generated per Stage 2
└── documents.zip                # generated by Stage 3
```

Stage 1 creates `output/` if absent. Stage 3 always creates `documents.zip`
containing all PDFs that were successfully produced in Stage 2 (even if some
products failed — SC-005).

**Rationale**: A single flat `output/` directory is simple to gitignore, mount
in Docker, and reference in CI artifact configuration. Separating `.adoc` and
`.pdf` into subdirectories adds no value for this use case.

**Alternatives considered**:
- `output/adoc/` + `output/pdf/` subdirectories — rejected (unnecessary nesting).
- Writing `.adoc` alongside source files in `infra/` — rejected (pollutes data dir).

---

## 6. Docker Build Environment

**Decision**: Provide a `Dockerfile` at repo root extending
`asciidoctor/docker-asciidoctor` with Python 3.11 and mermaid-cli.

```dockerfile
FROM asciidoctor/docker-asciidoctor:latest
RUN apk add --no-cache python3 py3-pip \
    && npm install -g @mermaid-js/mermaid-cli
```

README `docker run` command (FR-021):
```bash
docker build -t infra-sizing-builder .
docker run --rm -v "$(pwd):/repo" -w /repo infra-sizing-builder python3 build.py
```

**Rationale**: `asciidoctor/docker-asciidoctor` bundles asciidoctor-pdf and
asciidoctor-diagram. Python 3.11 is added via Alpine's package manager.
mermaid-cli is installed globally via npm (already present in the base image).
This keeps the `Dockerfile` minimal — two `RUN` instructions.

**Alternatives considered**:
- Using a Python base image and installing Ruby/asciidoctor from scratch —
  rejected (far more complex, larger image).
- Pinning to a specific `asciidoctor/docker-asciidoctor` tag — deferred to
  implementation; `latest` acceptable for initial release, pin if CI drift observed.

---

## 7. Error Accumulation Pattern

**Decision**: Use a `list[tuple[str, str]]` of `(product_shortname, error_message)`
pairs accumulated across all stages. Printed together at end of build. Exit 1 if
non-empty, exit 0 otherwise.

```python
errors: list[tuple[str, str]] = []

def run_build(repo_root: Path) -> int:
    errors = []
    successful_pdfs = []
    # Stage 1 + 2: per-product, append to errors on failure
    # Stage 3: archive successful_pdfs
    if errors:
        for shortname, msg in errors:
            print(f"ERROR [{shortname}]: {msg}", file=sys.stderr)
        return 1
    return 0
```

**Fatal errors** (halt entire build immediately, no archive produced):
- `theme.yml` absent (FR-015)
- `infra/products.json` absent or malformed JSON (FR-022)

**Product-level errors** (fail that product, continue — FR-008a):
- Product folder missing (FR-023)
- Server with empty disk list (FR-024)
- Product has no sizes / size has no flavours / flavour has no servers
- Missing prefix/suffix file referenced in meta.json (FR-015a)
- asciidoctor-pdf non-zero exit (Stage 2 failure)

**Rationale**: Centralised error accumulation matches FR-008a exactly.
Fatal vs. product-level distinction mirrors the same pattern used for `theme.yml`.

---

## 9. TypedValue: Static vs Dynamic Quantities

**Decision**: CPU, memory, and disk-partition size are modelled as `TypedValue`
objects — `{ "type": "static", "value": <number>, "unit": "<string>" }` or
`{ "type": "dynamic", "formula": "<string>", "unit": "<string>" }`. The unit
is stored alongside the value, not embedded in a free-text string.

**Rationale**: Separating value from unit enables consistent rendering without
string parsing. Dynamic formulas are descriptive strings (e.g. `"n × 4"`) that
express a scaling relationship; they are rendered verbatim in the PDF — the
build tool does not evaluate them. This design is forward-compatible with future
tooling that might compute or validate formula outputs.

**Rendering**:
- Static: `int(value) if value.is_integer() else value`, then `"{v} {unit}"` →
  `8 vCPU`, `32 GB`, `0.5 TB`
- Dynamic: `"{formula} {unit}"` → `n × 4 vCPU`, `n × 8 GB`

**CPU + Clocking merge**: Always rendered as a single column — `{cpu.render()} ({cpu_clocking})`.
Column header in AsciiDoc table is `CPU`. There is no separate CPU Clocking column.

**Count column suppression**: Evaluated per flavour table.
`suppress = all(s.count == 1 for s in flavour.servers)`.
When suppressed, column is omitted from both header and all rows.

**Alternatives considered**:
- Free-text strings with embedded units (previous design) — rejected because
  reliable parsing of `"8 vCPU"` or `"32 GB"` would require fragile regex;
  programmatic rendering is cleaner.
- Separate `value`, `unit`, `formula` top-level fields (flat structure) —
  rejected; nesting under `type` makes the discriminated union intent explicit.
- Enum type constants (`STATIC`, `DYNAMIC`) — rejected in favour of lowercase
  strings for JSON readability and round-trip simplicity.

---

## 8. Testing Strategy

**Decision**:
- **Unit tests** (`tests/unit/`): test `loader.py` validation logic and
  `renderer.py` AsciiDoc string output against `tests/fixtures/minimal-infra/`
  data. No asciidoctor toolchain required.
- **Integration tests** (`tests/integration/`): run full `build.py` pipeline
  against `tests/fixtures/minimal-infra/` and verify PDF and ZIP are produced.
  Marked `@pytest.mark.integration`; skipped by default in local runs; always
  run in CI inside the Docker container.

**pytest configuration** (`pytest.ini` or `pyproject.toml`):
```ini
[pytest]
markers =
    integration: requires asciidoctor toolchain (run in CI/Docker only)
```

**Rationale**: Separating unit and integration tests keeps local development fast
while ensuring the full pipeline is validated in CI where the toolchain is available.

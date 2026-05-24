# Quickstart: Infrastructure Sizing Document Export

**Phase 1 output** | **Branch**: `001-infra-sizing-doc-export`

---

## Prerequisites

- Docker installed (for local builds)
- Git (to version infrastructure definitions)

No local Ruby, Python, or Node.js installation required — everything runs inside
the provided Docker container.

---

## 1. Build the Docker Image (once)

From the repository root:

```bash
docker build -t infra-sizing-builder .
```

This builds a container based on `asciidoctor/docker-asciidoctor` extended with
Python 3.11 and mermaid-cli. Subsequent builds reuse the cached layers.

---

## 2. Provide a Theme

Place a `theme.yml` at the repository root. This file controls fonts, colours,
and layout for all generated PDFs. The build halts if this file is absent.

A minimal starter theme:

```yaml
extends: default
base:
  font_family: Helvetica
```

See [Asciidoctor PDF Theming Guide](https://docs.asciidoctor.org/pdf-converter/latest/theme/)
for the full reference.

---

## 3. Define Your Infrastructure

Create the `infra/` directory tree (see `docs/infra-sizing-doc-export/file-structure.md`
for the full layout). Minimum viable structure for one product, one size, one flavour:

```
infra/
├── products.json
├── preamble.adoc
├── suffix.adoc
└── my-product/
    ├── meta.json
    ├── sizes.json
    ├── preamble.adoc
    ├── suffix.adoc
    └── standard/
        ├── meta.json
        ├── flavours.json
        └── appserver/
            ├── meta.json
            └── servers.json
```

**`infra/products.json`**:
```json
[{ "shortname": "my-product", "display_name": "My Product" }]
```

**`infra/my-product/sizes.json`**:
```json
[{ "shortname": "standard", "display_name": "Standard" }]
```

**`infra/my-product/meta.json`**:
```json
{ "preamble": "preamble.adoc", "suffix": "suffix.adoc" }
```

**`infra/my-product/standard/meta.json`**:
```json
{ "prefix_text": "", "suffix_text": "" }
```

**`infra/my-product/standard/flavours.json`**:
```json
[{ "shortname": "appserver", "display_name": "Application Server" }]
```

**`infra/my-product/standard/appserver/meta.json`**:
```json
{}
```

**`infra/my-product/standard/appserver/servers.json`**:
```json
[
  {
    "system": "Application Server",
    "count": 2,
    "cpu": "8 vCPU",
    "cpu_clocking": "3.0 GHz",
    "memory": "32 GB",
    "disk": [
      { "size": "100 GB", "performance": "NVMe SSD", "comment": "OS" },
      { "size": "500 GB", "performance": "NVMe SSD", "comment": "Data" }
    ],
    "network": ["2× 10GbE"],
    "software": ["OpenJDK 17", "NGINX"]
  }
]
```

Add placeholder content to the `.adoc` files (they can be empty for a first run):
```bash
touch infra/preamble.adoc infra/suffix.adoc
touch infra/my-product/preamble.adoc infra/my-product/suffix.adoc
```

---

## 4. Run the Build

```bash
docker run --rm \
  -v "$(pwd):/repo" \
  -w /repo \
  infra-sizing-builder \
  python3 build.py
```

On success, outputs appear in `output/`:
- `output/my-product.adoc` — generated AsciiDoc source
- `output/my-product.pdf` — rendered PDF
- `output/documents.zip` — ZIP archive containing the PDF

---

## 5. Common Errors

| Error message | Cause | Fix |
|---------------|-------|-----|
| `FATAL: theme.yml not found` | `theme.yml` missing at repo root | Create `theme.yml` |
| `FATAL: infra/products.json missing or invalid` | Registry file absent or malformed JSON | Create/fix `infra/products.json` |
| `ERROR [my-product]: folder not found` | Shortname in `products.json` has no matching directory | Create `infra/my-product/` |
| `ERROR [my-product]: no sizes defined` | `sizes.json` empty or missing entries | Add at least one size |
| `ERROR [my-product]: server has no disk partitions` | `disk` array empty in `servers.json` | Add at least one partition |
| `ERROR [my-product]: preamble file not found` | Path in `meta.json` doesn't exist | Create the referenced `.adoc` file |

---

## 6. CI/CD

Both GitLab CI and GitHub Actions pipelines are provided. They run the same
`python3 build.py` command inside the Docker container and publish PDF and ZIP
as build artifacts. See `contracts/build-contract.md` for the full pipeline
configuration.

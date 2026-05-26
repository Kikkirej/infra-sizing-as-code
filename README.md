# Infrastructure Sizing Document Export

Generates infrastructure sizing PDFs from declarative JSON + AsciiDoc definitions.

## Quick Start

```bash
# Build the Docker image (once)
docker build -t infra-sizing-builder .

# Run a build from the repo root
docker run --rm \
  -v "$(pwd):/repo" \
  -w /repo \
  infra-sizing-builder \
  python3 build.py
```

Generated PDFs and the `documents.zip` archive are written to `output/`.

## Adding Infrastructure Definitions

1. Add an entry to `infra/products.json`
2. Create `infra/{shortname}/` with `meta.json`, `sizes.json`, `prefix.adoc`, `suffix.adoc`
3. Add sizes and flavours following the directory structure
4. Run the build

See [docs/infra-sizing-doc-export/file-structure.md](docs/infra-sizing-doc-export/file-structure.md) for the complete file structure reference.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All products built successfully |
| 1 | One or more products failed, or fatal error |

## Requirements

- `theme.yml` at repo root
- `infra/products.json` present and valid JSON
- asciidoctor-pdf with asciidoctor-diagram (provided by the Docker image)
- Python 3.11+

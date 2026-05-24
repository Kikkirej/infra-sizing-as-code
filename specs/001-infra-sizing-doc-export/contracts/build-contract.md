# Build Invocation Contract

**Phase 1 output** | **Branch**: `001-infra-sizing-doc-export`

---

## CLI Invocation

```bash
python build.py
```

No required arguments. The script always runs all three stages sequentially.

**Working directory**: Must be the repository root (the directory containing
`infra/`, `theme.yml`, and `build.py`).

**No CLI flags or subcommands** in the initial release. Future flags (e.g.
`--product`, `--dry-run`) are out of scope for this feature.

---

## Preconditions

The following must be true before invoking `build.py`:

| Precondition | Effect if violated |
|--------------|--------------------|
| `theme.yml` present at repo root | Fatal — build halts immediately |
| `infra/products.json` present and valid JSON | Fatal — build halts immediately |
| asciidoctor-pdf in `PATH` | Fatal — Stage 2 subprocess fails for all products |
| asciidoctor-diagram Ruby gem loadable | Fatal — asciidoctor-pdf `-r` flag fails |
| `mmdc` in `PATH` (if any flavour has mermaid image) | Product-level failure |
| Python 3.11+ | Fatal — import errors for 3.11-specific syntax |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All products built and archived successfully |
| 1 | One or more products failed, or fatal error occurred |

---

## Standard Streams

| Stream | Content |
|--------|---------|
| stdout | Progress messages (one line per product per stage, e.g. `[generate] product-a … OK`) |
| stderr | Error messages in the format `ERROR [product-shortname]: <message>`; fatal errors also go to stderr |

---

## Outputs

| Path | Description | Created when |
|------|-------------|-------------|
| `output/{shortname}.adoc` | Generated AsciiDoc source for product | Stage 1 success |
| `output/{shortname}.pdf` | Rendered PDF for product | Stage 2 success |
| `output/documents.zip` | ZIP archive of all successful PDFs | Stage 3 (always, if ≥1 PDF) |

The `output/` directory is created by Stage 1 if absent. It is not cleared
between runs; re-running overwrites existing files.

If all products fail Stage 2, Stage 3 runs but produces an empty or absent
archive (no PDFs to include). The build still exits with code 1.

---

## Docker Invocation (FR-021)

```bash
# Build the local image (once)
docker build -t infra-sizing-builder .

# Run a build (from repo root)
docker run --rm \
  -v "$(pwd):/repo" \
  -w /repo \
  infra-sizing-builder \
  python3 build.py
```

The `Dockerfile` at repo root extends `asciidoctor/docker-asciidoctor` and
adds Python 3.11 and `@mermaid-js/mermaid-cli`.

---

## CI/CD Integration

Both platforms invoke the same command inside the Docker container image.

### GitLab CI (`.gitlab-ci.yml`)

```yaml
stages:
  - build

build-docs:
  image: infra-sizing-builder  # or build from Dockerfile in CI
  script:
    - python3 build.py
  artifacts:
    paths:
      - output/*.pdf
      - output/documents.zip
    when: always   # collect artifacts even on partial failure
```

### GitHub Actions (`.github/workflows/build.yml`)

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t infra-sizing-builder .
      - name: Run build
        run: |
          docker run --rm -v "${{ github.workspace }}:/repo" \
            -w /repo infra-sizing-builder python3 build.py
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: documents
          path: |
            output/*.pdf
            output/documents.zip
```

# Infrastructure Definition File Structure

## Directory Layout

```
infra/
├── products.json              # Registry of all products
├── preamble.adoc              # Common preamble included in every document
├── suffix.adoc                # Common suffix included in every document
└── {product-shortname}/
    ├── meta.json              # Product metadata (preamble/suffix paths)
    ├── sizes.json             # Registry of sizes for this product
    ├── preamble.adoc          # Product-specific preamble
    ├── suffix.adoc            # Product-specific suffix
    └── {size-shortname}/
        ├── meta.json          # Size metadata (optional prefix/suffix text)
        ├── flavours.json      # Registry of flavours for this size
        └── {flavour-shortname}/
            ├── meta.json      # Flavour metadata (optional image)
            ├── preamble.adoc  # Optional flavour preamble
            ├── suffix.adoc    # Optional flavour suffix
            └── servers.json   # List of servers for this flavour
```

## File Naming Conventions

- `shortname` values: lowercase, hyphen-separated, no spaces (e.g. `product-a`, `size-s`)
- Registry files are always named `products.json`, `sizes.json`, `flavours.json`
- Metadata files are always named `meta.json`
- AsciiDoc files use `.adoc` extension

## Registry File Schemas

### `infra/products.json`

```json
[
  { "shortname": "product-a", "display_name": "Product A" }
]
```

### `infra/{product}/sizes.json`

```json
[
  { "shortname": "small", "display_name": "50 Users" }
]
```

### `infra/{product}/{size}/flavours.json`

```json
[
  { "shortname": "appserver", "display_name": "Application Server" }
]
```

### `infra/{product}/meta.json`

```json
{ "preamble": "preamble.adoc", "suffix": "suffix.adoc" }
```

### `infra/{product}/{size}/meta.json`

```json
{ "prefix_text": "Optional text before tables.", "suffix_text": "Optional text after tables." }
```

### `infra/{product}/{size}/{flavour}/meta.json`

```json
{ "image": { "type": "file", "value": "architecture.png" } }
```

`type` is `"file"` (static image) or `"mermaid"` (`.mmd` diagram). Omit the `image` key entirely for no image.

### `infra/{product}/{size}/{flavour}/servers.json`

```json
[
  {
    "system": "Web Server",
    "count": 3,
    "cpu": "4 vCPU",
    "cpu_clocking": "3.2 GHz",
    "memory": "32 GB",
    "disk": [
      { "size": "500 GB", "performance": "NVMe SSD", "comment": "OS + App" }
    ],
    "network": ["2× 10GbE"],
    "software": ["NGINX 1.25"],
    "comment": "Primary web tier"
  }
]
```

Required fields: `system`, `cpu`, `cpu_clocking`, `memory`, `disk` (min 1 entry).
Optional fields with defaults: `count` (1), `network` ([]), `software` ([]), `comment` ("").

## Build Output Structure

```
output/
├── {product-shortname}.adoc   # Generated AsciiDoc source
├── {product-shortname}.pdf    # Rendered PDF
└── documents.zip              # Archive of all successful PDFs
```

The `output/` directory is gitignored. Re-running the build overwrites existing files.

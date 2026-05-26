# Data Model: MCP Sizing Server

The MCP server is read-only. It exposes a subset of the existing infra data model as clean response shapes, stripping all editor-specific metadata (change states, prefix/suffix content, images).

## Hierarchy

```
Product
└── Size (1..*)
    └── Flavour (1..*)
        └── Server (1..*)
            ├── CPU (TypedValue)
            ├── Memory (TypedValue)
            └── Disk Partition (1..*)
```

## Response Shapes

### ProductSummary
Returned by `list_products`.

| Field        | Type   | Description                        |
|-------------|--------|------------------------------------|
| shortname   | string | Unique identifier, e.g. `acme-crm` |
| display_name| string | Human-readable name                |

### SizeSummary
Returned by `list_sizes`.

| Field        | Type   | Description                                    |
|-------------|--------|------------------------------------------------|
| shortname   | string | Unique within product, e.g. `small`            |
| display_name| string | Human-readable name, e.g. `Small (100 Users)`  |

### FlavourSummary
Returned by `list_flavours`.

| Field        | Type   | Description                                        |
|-------------|--------|----------------------------------------------------|
| shortname   | string | Unique within size, e.g. `appserver`               |
| display_name| string | Human-readable name, e.g. `Application Servers`    |

### FlavourSpec
Returned by `get_flavour_spec`. Full hardware specification for one flavour.

| Field        | Type           | Description                            |
|-------------|----------------|----------------------------------------|
| shortname   | string         | Flavour identifier                     |
| display_name| string         | Human-readable name                    |
| servers     | list[Server]   | One or more server definitions         |

### Server

| Field        | Type             | Description                                        |
|-------------|------------------|----------------------------------------------------|
| system      | string           | Descriptive name, e.g. `Application Server`        |
| count       | int              | Number of instances                                |
| cpu         | TypedValue       | CPU specification                                  |
| cpu_clocking| string           | Clock speed, e.g. `3.0 GHz`                        |
| memory      | TypedValue       | RAM specification                                  |
| disk        | list[Partition]  | Disk partitions                                    |
| network     | list[string]     | Network interfaces, e.g. `["2× 10GbE"]`            |
| software    | list[string]     | Required software, e.g. `["OpenJDK 17"]`           |
| comment     | string           | Optional notes                                     |

### TypedValue

| Field   | Type   | Present when     | Description                    |
|---------|--------|------------------|--------------------------------|
| type    | string | always           | `"static"` or `"dynamic"`      |
| unit    | string | always           | e.g. `vCPU`, `GB`              |
| value   | float  | type = static    | Concrete numeric value         |
| formula | string | type = dynamic   | Expression for computed values |

### Partition

| Field       | Type       | Description                          |
|-------------|------------|--------------------------------------|
| size        | TypedValue | Disk size                            |
| performance | string     | Storage class, e.g. `NVMe SSD`       |
| comment     | string     | Optional purpose note, e.g. `OS`     |

## Error Responses

All tools return a plain string on failure. The string identifies the failing level:

| Scenario                    | Error text pattern                                          |
|----------------------------|-------------------------------------------------------------|
| Product not found          | `"Product 'X' not found"`                                   |
| Size not found for product | `"Size 'Y' not found for product 'X'"`                      |
| Flavour not found          | `"Flavour 'Z' not found for product 'X' size 'Y'"`          |
| infra/ missing at startup  | `"infra/products.json not found at <path> — check REPO_ROOT"` |

## Identity Rules

- Products are uniquely identified by `shortname` within `infra/products.json`.
- Sizes are uniquely identified by `shortname` within a product's `sizes.json`.
- Flavours are uniquely identified by `shortname` within a size's `flavours.json`.
- Short names are stable file-system identifiers; display names may change.

# MCP Tool Contracts: Infrastructure Sizing Server

Transport: **HTTP / SSE**
Base URL: `http://localhost:8000/mcp`
SSE endpoint: `http://localhost:8000/mcp/sse`

All tools are read-only. No tool modifies the repository.

---

## Tool 1: `list_products`

List all infrastructure products available in the repository.

**Inputs**: none

**Returns** (success): JSON array of ProductSummary objects
```json
[
  { "shortname": "acme-crm", "display_name": "ACME CRM Platform" },
  { "shortname": "acme-erp", "display_name": "ACME ERP Platform" }
]
```

**Returns** (empty): `[]` — `infra/products.json` exists but contains no entries

---

## Tool 2: `list_sizes`

List all size tiers available for a given product.

**Inputs**:

| Parameter | Type   | Required | Description                        |
|-----------|--------|----------|------------------------------------|
| product   | string | yes      | Product short name, e.g. `acme-crm` |

**Returns** (success): JSON array of SizeSummary objects
```json
[
  { "shortname": "small",  "display_name": "Small (100 Users)" },
  { "shortname": "medium", "display_name": "Medium (500 Users)" },
  { "shortname": "large",  "display_name": "Large (2000 Users)" }
]
```

**Returns** (error): plain string — `"Product 'X' not found"`

---

## Tool 3: `list_flavours`

List all flavours (component groups) available within a given product and size combination.

**Inputs**:

| Parameter | Type   | Required | Description                          |
|-----------|--------|----------|--------------------------------------|
| product   | string | yes      | Product short name, e.g. `acme-crm`  |
| size      | string | yes      | Size short name, e.g. `small`        |

**Returns** (success): JSON array of FlavourSummary objects
```json
[
  { "shortname": "appserver", "display_name": "Application Servers" },
  { "shortname": "dbserver",  "display_name": "Database Servers" }
]
```

**Returns** (error): plain string — `"Product 'X' not found"` or `"Size 'Y' not found for product 'X'"`

---

## Tool 4: `get_flavour_spec`

Retrieve the full hardware specification for a specific flavour.

**Inputs**:

| Parameter | Type   | Required | Description                             |
|-----------|--------|----------|-----------------------------------------|
| product   | string | yes      | Product short name, e.g. `acme-crm`    |
| size      | string | yes      | Size short name, e.g. `small`           |
| flavour   | string | yes      | Flavour short name, e.g. `appserver`    |

**Returns** (success): JSON object — FlavourSpec
```json
{
  "shortname": "appserver",
  "display_name": "Application Servers",
  "servers": [
    {
      "system": "Application Server",
      "count": 2,
      "cpu": { "type": "static", "value": 8, "unit": "vCPU" },
      "cpu_clocking": "3.0 GHz",
      "memory": { "type": "static", "value": 32, "unit": "GB" },
      "disk": [
        { "size": { "type": "static", "value": 100, "unit": "GB" }, "performance": "NVMe SSD", "comment": "OS" },
        { "size": { "type": "static", "value": 200, "unit": "GB" }, "performance": "NVMe SSD", "comment": "App data" }
      ],
      "network": ["2× 10GbE"],
      "software": ["OpenJDK 17", "NGINX 1.25"],
      "comment": "Active/active pair"
    }
  ]
}
```

**Returns** (error): plain string — level-specific not-found message (see data-model.md)

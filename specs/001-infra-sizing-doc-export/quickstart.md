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

## 3. Define Your Infrastructure (Two-Product Example)

The following example defines **two products** (`acme-crm` and `acme-erp`), each
with **multiple sizes** and **multiple flavours** per size. This reflects a
typical deployment where different scale tiers add components.

### Directory Layout

```
infra/
├── products.json
├── prefix.adoc
├── suffix.adoc
│
├── acme-crm/
│   ├── meta.json
│   ├── sizes.json
│   ├── prefix.adoc
│   ├── suffix.adoc
│   ├── small/
│   │   ├── meta.json
│   │   ├── flavours.json
│   │   ├── appserver/
│   │   │   ├── meta.json
│   │   │   └── servers.json
│   │   └── dbserver/
│   │       ├── meta.json
│   │       └── servers.json
│   ├── medium/
│   │   ├── meta.json
│   │   ├── flavours.json
│   │   ├── appserver/
│   │   │   ├── meta.json
│   │   │   └── servers.json
│   │   ├── dbserver/
│   │   │   ├── meta.json
│   │   │   └── servers.json
│   │   └── cacheserver/
│   │       ├── meta.json
│   │       └── servers.json
│   └── large/
│       ├── meta.json
│       ├── flavours.json
│       ├── appserver/
│       │   ├── meta.json
│       │   └── servers.json
│       ├── dbserver/
│       │   ├── meta.json
│       │   └── servers.json
│       ├── cacheserver/
│       │   ├── meta.json
│       │   └── servers.json
│       └── loadbalancer/
│           ├── meta.json
│           └── servers.json
│
└── acme-erp/
    ├── meta.json
    ├── sizes.json
    ├── prefix.adoc
    ├── suffix.adoc
    ├── standard/
    │   ├── meta.json
    │   ├── flavours.json
    │   ├── appserver/
    │   │   ├── meta.json
    │   │   └── servers.json
    │   └── dbserver/
    │       ├── meta.json
    │       └── servers.json
    └── enterprise/
        ├── meta.json
        ├── flavours.json
        ├── appserver/
        │   ├── meta.json
        │   └── servers.json
        ├── dbserver/
        │   ├── meta.json
        │   └── servers.json
        └── analyticsserver/
            ├── meta.json
            └── servers.json
```

### Registry Files

**`infra/products.json`** — lists both products in display order:
```json
[
  { "shortname": "acme-crm", "display_name": "ACME CRM Platform" },
  { "shortname": "acme-erp", "display_name": "ACME ERP Platform" }
]
```

**`infra/acme-crm/sizes.json`** — three CRM tiers:
```json
[
  { "shortname": "small",  "display_name": "Small (100 Users)"  },
  { "shortname": "medium", "display_name": "Medium (500 Users)" },
  { "shortname": "large",  "display_name": "Large (2000 Users)" }
]
```

**`infra/acme-erp/sizes.json`** — two ERP tiers:
```json
[
  { "shortname": "standard",   "display_name": "Standard (250 Users)"    },
  { "shortname": "enterprise", "display_name": "Enterprise (1000 Users)" }
]
```

**`infra/acme-crm/small/flavours.json`**:
```json
[
  { "shortname": "appserver", "display_name": "Application Servers" },
  { "shortname": "dbserver",  "display_name": "Database Servers"    }
]
```

**`infra/acme-crm/medium/flavours.json`** — adds a cache tier:
```json
[
  { "shortname": "appserver",   "display_name": "Application Servers" },
  { "shortname": "dbserver",    "display_name": "Database Servers"    },
  { "shortname": "cacheserver", "display_name": "Cache Servers"       }
]
```

**`infra/acme-crm/large/flavours.json`** — adds load balancing:
```json
[
  { "shortname": "appserver",   "display_name": "Application Servers" },
  { "shortname": "dbserver",    "display_name": "Database Servers"    },
  { "shortname": "cacheserver", "display_name": "Cache Servers"       },
  { "shortname": "loadbalancer","display_name": "Load Balancers"      }
]
```

**`infra/acme-erp/standard/flavours.json`**:
```json
[
  { "shortname": "appserver", "display_name": "Application Servers" },
  { "shortname": "dbserver",  "display_name": "Database Servers"    }
]
```

**`infra/acme-erp/enterprise/flavours.json`** — adds analytics:
```json
[
  { "shortname": "appserver",      "display_name": "Application Servers" },
  { "shortname": "dbserver",       "display_name": "Database Servers"    },
  { "shortname": "analyticsserver","display_name": "Analytics Servers"   }
]
```

### Meta Files

**`infra/acme-crm/meta.json`**:
```json
{ "prefix": "prefix.adoc", "suffix": "suffix.adoc" }
```

**`infra/acme-erp/meta.json`**:
```json
{ "prefix": "prefix.adoc", "suffix": "suffix.adoc" }
```

**`infra/acme-crm/small/meta.json`** — size prefix/suffix text:
```json
{
  "prefix_text": "This tier is designed for up to 100 concurrent users with moderate data volumes.",
  "suffix_text": "For larger deployments, see the Medium or Large sizing tiers."
}
```

**`infra/acme-crm/medium/meta.json`**:
```json
{
  "prefix_text": "This tier scales to 500 concurrent users and introduces dedicated caching.",
  "suffix_text": ""
}
```

**`infra/acme-crm/large/meta.json`**:
```json
{
  "prefix_text": "This tier handles 2000+ concurrent users with full HA and load balancing.",
  "suffix_text": "Contact your account manager for custom sizing beyond this tier."
}
```

**`infra/acme-erp/standard/meta.json`**:
```json
{
  "prefix_text": "Standard ERP deployment for up to 250 named users.",
  "suffix_text": ""
}
```

**`infra/acme-erp/enterprise/meta.json`**:
```json
{
  "prefix_text": "Enterprise deployment with integrated analytics for up to 1000 named users.",
  "suffix_text": "Dedicated DBA support recommended for this sizing."
}
```

All flavour `meta.json` files without an image are simply `{}`.

### Server Definitions

**`infra/acme-crm/small/appserver/servers.json`** — `count: 2`, shown inline as `[2]` in the System cell:
```json
[
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
```

Generated AsciiDoc (count `[2]` in System cell; software + network + comment merged in Comment; Disk as nested table):

```asciidoc
[cols="15,14,13,43,33",options="header"]
|===
| System | CPU | Memory | Disk | Comment

| Application Server [2] | 8 vCPU (3.0 GHz) | 32 GB
a|
[cols="3,3,3",options="header"]
!===
! Size ! Perform- +
ance ! Comment/ +
Usage
! 100 GB ! NVMe SSD ! OS
! 200 GB ! NVMe SSD ! App data
!===
a|
* OpenJDK 17
* NGINX 1.25
* 2× 10GbE

Active/active pair

|===
```

**`infra/acme-crm/small/dbserver/servers.json`** — `count: 1`, no count annotation; software + network + comment merged:
```json
[
  {
    "system": "Primary Database",
    "count": 1,
    "cpu": { "type": "static", "value": 16, "unit": "vCPU" },
    "cpu_clocking": "3.4 GHz",
    "memory": { "type": "static", "value": 64, "unit": "GB" },
    "disk": [
      { "size": { "type": "static", "value": 100, "unit": "GB" },  "performance": "NVMe SSD",     "comment": "OS"   },
      { "size": { "type": "static", "value": 1,   "unit": "TB" },  "performance": "NVMe SSD",     "comment": "Data" },
      { "size": { "type": "static", "value": 500, "unit": "GB" },  "performance": "7200 RPM HDD", "comment": "Logs" }
    ],
    "network": ["2× 10GbE"],
    "software": ["PostgreSQL 16"],
    "comment": ""
  },
  {
    "system": "Replica Database",
    "count": 1,
    "cpu": { "type": "static", "value": 16, "unit": "vCPU" },
    "cpu_clocking": "3.4 GHz",
    "memory": { "type": "static", "value": 64, "unit": "GB" },
    "disk": [
      { "size": { "type": "static", "value": 100, "unit": "GB" },  "performance": "NVMe SSD",     "comment": "OS"   },
      { "size": { "type": "static", "value": 1,   "unit": "TB" },  "performance": "NVMe SSD",     "comment": "Data" },
      { "size": { "type": "static", "value": 500, "unit": "GB" },  "performance": "7200 RPM HDD", "comment": "Logs" }
    ],
    "network": ["2× 10GbE"],
    "software": ["PostgreSQL 16"],
    "comment": "Hot standby"
  }
]
```

Generated AsciiDoc (no count annotation since `count: 1`; Disk as nested table; software + network in Comment):

```asciidoc
[cols="15,14,13,43,33",options="header"]
|===
| System | CPU | Memory | Disk | Comment

| Primary Database | 16 vCPU (3.4 GHz) | 64 GB
a|
[cols="3,3,3",options="header"]
!===
! Size ! Perform- +
ance ! Comment/ +
Usage
! 100 GB ! NVMe SSD ! OS
! 1 TB ! NVMe SSD ! Data
! 500 GB ! 7200 RPM HDD ! Logs
!===
a|
* PostgreSQL 16
* 2× 10GbE

| Replica Database | 16 vCPU (3.4 GHz) | 64 GB
a|
[cols="3,3,3",options="header"]
!===
! Size ! Perform- +
ance ! Comment/ +
Usage
! 100 GB ! NVMe SSD ! OS
! 1 TB ! NVMe SSD ! Data
! 500 GB ! 7200 RPM HDD ! Logs
!===
a|
* PostgreSQL 16
* 2× 10GbE

Hot standby

|===
```

**`infra/acme-crm/medium/cacheserver/servers.json`** — new flavour added at Medium tier:
```json
[
  {
    "system": "Cache Node",
    "count": 3,
    "cpu": { "type": "static", "value": 8, "unit": "vCPU" },
    "cpu_clocking": "3.0 GHz",
    "memory": { "type": "static", "value": 128, "unit": "GB" },
    "disk": [
      { "size": { "type": "static", "value": 100, "unit": "GB" }, "performance": "NVMe SSD", "comment": "OS" }
    ],
    "network": ["2× 25GbE"],
    "software": ["Redis 7"],
    "comment": "Clustered, in-memory only"
  }
]
```

**`infra/acme-crm/large/loadbalancer/servers.json`** — new flavour added at Large tier:
```json
[
  {
    "system": "Load Balancer",
    "count": 2,
    "cpu": { "type": "static", "value": 4, "unit": "vCPU" },
    "cpu_clocking": "2.8 GHz",
    "memory": { "type": "static", "value": 16, "unit": "GB" },
    "disk": [
      { "size": { "type": "static", "value": 100, "unit": "GB" }, "performance": "NVMe SSD", "comment": "OS" }
    ],
    "network": ["4× 25GbE"],
    "software": ["HAProxy 2.8"],
    "comment": "Active/passive HA pair"
  }
]
```

**`infra/acme-erp/enterprise/analyticsserver/servers.json`** — dynamic memory shows formula rendering:
```json
[
  {
    "system": "Analytics Server",
    "count": 2,
    "cpu": { "type": "static", "value": 32, "unit": "vCPU" },
    "cpu_clocking": "3.5 GHz",
    "memory": { "type": "static", "value": 256, "unit": "GB" },
    "disk": [
      { "size": { "type": "static",  "value": 100,  "unit": "GB" }, "performance": "NVMe SSD",     "comment": "OS"           },
      { "size": { "type": "static",  "value": 4,    "unit": "TB" }, "performance": "NVMe SSD",     "comment": "Hot storage"  },
      { "size": { "type": "dynamic", "formula": "n × 20", "unit": "TB" }, "performance": "7200 RPM HDD", "comment": "Cold archive (per retention policy)" }
    ],
    "network": ["2× 25GbE"],
    "software": ["Apache Spark 3.5", "Hadoop 3.3"],
    "comment": "HDFS namenode + Spark master on node 1"
  }
]
```

The dynamic partition renders in the nested Disk table as:
```asciidoc
! n × 20 TB ! 7200 RPM HDD ! Cold archive (per retention policy)
```

**Fallback rendering** (if nested tables are visually unsatisfactory): the Disk cell
would show `24.1 TB + variable (3 partitions)` and a separate titled table would
follow the server table:
```asciidoc
.Partitions — Analytics Server
[cols="3,3,3",options="header"]
|===
| Size | Performance | Comment
| 100 GB | NVMe SSD | OS
| 4 TB | NVMe SSD | Hot storage
| n × 20 TB | 7200 RPM HDD | Cold archive (per retention policy)
|===
```

### Prefix and Suffix Files

Create placeholder `.adoc` files for the common sections and each product:

```bash
touch infra/prefix.adoc infra/suffix.adoc
touch infra/acme-crm/prefix.adoc infra/acme-crm/suffix.adoc
touch infra/acme-erp/prefix.adoc infra/acme-erp/suffix.adoc
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

On success, the `output/` directory contains:

```
output/
├── acme-crm.adoc
├── acme-crm.pdf
├── acme-erp.adoc
├── acme-erp.pdf
└── documents.zip        ← contains both PDFs
```

The `acme-crm.pdf` has three size sections (Small / Medium / Large), each with
its own flavour subsections and server tables. The `acme-erp.pdf` has two size
sections (Standard / Enterprise). Both PDFs share the same `infra/prefix.adoc`
and `infra/suffix.adoc` content.

---

## 5. Common Errors

| Error message | Cause | Fix |
|---------------|-------|-----|
| `FATAL: theme.yml not found` | `theme.yml` missing at repo root | Create `theme.yml` |
| `FATAL: infra/products.json missing or invalid` | Registry file absent or malformed JSON | Create/fix `infra/products.json` |
| `ERROR [acme-crm]: folder not found` | Shortname in `products.json` has no matching directory | Create `infra/acme-crm/` |
| `ERROR [acme-crm]: no sizes defined` | `sizes.json` empty or missing entries | Add at least one size |
| `ERROR [acme-crm]: no flavours defined for size 'small'` | `flavours.json` empty | Add at least one flavour |
| `ERROR [acme-crm]: server has no disk partitions` | `disk` array empty in `servers.json` | Add at least one partition |
| `ERROR [acme-crm]: prefix file not found` | Path in `meta.json` doesn't exist on disk | Create the referenced `.adoc` file |

---

## 6. CI/CD

Both GitLab CI and GitHub Actions pipelines run the same `python3 build.py`
command inside the Docker container and publish PDFs and ZIP as build artifacts.
See `contracts/build-contract.md` for the full pipeline configuration.

# Feature Specification: MCP Sizing Server

**Feature Branch**: `003-mcp-sizing-server`

**Created**: 2026-05-26

**Status**: Draft

**Input**: User description: "add a MCP server to get the infrastructure sizing, write a document how to import it into cursor in the docs. it should be part of the backend."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Sizing via AI Assistant (Priority: P1)

A developer using Cursor (or any MCP-compatible AI assistant) wants to retrieve infrastructure sizing information for a specific product and tier without leaving their editor. They ask their AI assistant a natural-language question such as "What are the infrastructure requirements for ACME CRM in a medium deployment?" and receive the accurate, structured sizing data pulled live from the sizing repository.

**Why this priority**: This is the core value of the feature. It enables AI-assisted infrastructure planning directly from the source of truth — no copy-pasting from PDFs or manual lookups.

**Independent Test**: Can be fully tested by connecting a client to the MCP server and invoking a tool call to retrieve sizing data for a known product/tier combination, then verifying the returned data matches the repository contents.

**Acceptance Scenarios**:

1. **Given** the MCP server is running and a product/size/flavour combination exists, **When** a client requests the flavour specification, **Then** the server returns the complete flavour specification for that tier.
2. **Given** a client requests data using a non-existent product, size, or flavour, **When** the server processes the request, **Then** the server returns a clear error indicating which level of the hierarchy was not found.
3. **Given** the MCP server is running, **When** a client asks for available products, **Then** the server returns the full list of registered products with their display names.

---

### User Story 2 - Discover Available Products and Sizes (Priority: P2)

A developer wants to know which products and sizing tiers are available in the repository before querying details. They can ask their AI assistant "What products are available?" or "What sizes does ACME ERP come in?" and get an accurate answer.

**Why this priority**: Discovery is essential before querying details; without it, users would need to know product names and sizes in advance, greatly limiting the assistant's usefulness.

**Independent Test**: Can be fully tested by invoking the list-products, list-sizes, and list-flavours tools and verifying responses match the current `products.json`, per-product `sizes.json`, and per-size `flavours.json` files.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** a client requests all available products, **Then** the server returns a list of all products with their short names and display names.
2. **Given** a valid product short name, **When** a client requests available sizes for that product, **Then** the server returns all size tiers defined for that product.
3. **Given** a valid product and size, **When** a client requests available flavours for that combination, **Then** the server returns all flavours defined for that size.
4. **Given** an invalid product, size, or flavour, **When** a client requests discovery at that level, **Then** the server returns a level-specific not-found response.

---

### User Story 3 - Connect Cursor to the MCP Server (Priority: P3)

A new team member wants to set up Cursor to use the MCP server so their AI assistant can answer infrastructure sizing questions. They follow the provided documentation and complete the configuration without needing help from a colleague.

**Why this priority**: The server only delivers value if developers can connect to it. Documentation is the bridge between the backend capability and actual adoption.

**Independent Test**: Can be fully tested by following the documentation from start to finish on a clean Cursor installation and confirming that the AI assistant can answer a sizing question after setup.

**Acceptance Scenarios**:

1. **Given** a developer has Cursor installed and the MCP server running, **When** they follow the documentation step by step, **Then** the MCP server appears as a connected tool in Cursor's settings.
2. **Given** the MCP server is connected in Cursor, **When** the developer asks their AI assistant an infrastructure sizing question, **Then** the assistant uses the MCP server to provide an accurate answer.
3. **Given** a developer makes a configuration mistake, **When** they consult the documentation's troubleshooting section, **Then** they find guidance for the most common connection errors.

---

### Edge Cases

- **Missing `infra/` at startup**: The backend fails to start with a clear diagnostic error (see FR-010).
- **`sizes.json` references a missing directory**: Treated as a not-found response for that size — same level-specific error as FR-005.
- **Infra files being edited during a query**: Reads whatever is on disk at query time; partial reads are possible but acceptable for v1 local use.
- **Flavour directory present but contains no spec files**: Returns an empty flavour specification; no error raised.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The server MUST expose a tool to list all available products from the infrastructure repository.
- **FR-002**: The server MUST expose a tool to list all available size tiers for a given product.
- **FR-003**: The server MUST expose a tool to list all flavours (component groups) available within a given product/size combination.
- **FR-003a**: The server MUST expose a tool to retrieve the full hardware specification for a specific flavour within a given product and size tier, including all component details (CPU, RAM, disk, network, software).
- **FR-004**: The server MUST return structured, machine-readable responses suitable for AI assistant consumption.
- **FR-005**: The server MUST return a meaningful, level-specific error message when a requested product, size, or flavour does not exist (e.g., "Product 'X' not found", "Size 'Y' not found for product 'X'", "Flavour 'Z' not found for product 'X' size 'Y'").
- **FR-006**: The server MUST read sizing data from the existing `infra/` directory structure on every request — no in-memory caching — so that changes to infra files are reflected immediately without a server restart.
- **FR-007**: The MCP endpoint MUST be mounted into the existing web editor backend process — no separate process or port management is required; the endpoint becomes available automatically when the backend starts.
- **FR-007a**: The MCP server MUST communicate via HTTP/SSE transport, exposing a URL endpoint (e.g., `http://localhost:<PORT>/mcp`) that clients connect to over the network.
- **FR-008**: The documentation MUST be placed at `docs/mcp-server/` and MUST describe how to add the MCP server as a tool source in Cursor by providing the HTTP/SSE endpoint URL in Cursor's MCP settings, including a verification step confirming the connection works.
- **FR-009**: The documentation MUST include a troubleshooting section covering the most common connection and configuration issues.
- **FR-010**: The backend MUST validate that the `infra/` directory exists and contains at least one product at startup; if the check fails, the backend MUST refuse to start and output a clear diagnostic message identifying the missing or misconfigured path.

### Key Entities

- **Product**: A software product available for sizing (e.g., "ACME CRM Platform"), identified by a short name and human-readable display name.
- **Size Tier**: A deployment scale for a product (e.g., "Small – 100 Users"), identified by a short name within its product.
- **Flavour**: A category of infrastructure components within a size tier (e.g., "Application Servers", "Database Servers"). This is the canonical term used in the repository (`flavours.json`).
- **Flavour Specification**: The full hardware configuration for a specific flavour — including server count, CPU, RAM, disk layout, network, and software stack.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can retrieve complete sizing data for any valid product/size combination in under 2 seconds via the MCP server.
- **SC-002**: All products and sizes defined in the repository are discoverable through the MCP server without any manual configuration.
- **SC-003**: A developer with no prior knowledge of the project can connect Cursor to the MCP server and make a successful query by following the documentation alone, in under 10 minutes.
- **SC-004**: The MCP server returns a clear, actionable error message for 100% of invalid product or size requests.

## Clarifications

### Session 2026-05-26 (second run)

- Q: Should error handling cover invalid flavour requests, not just product/size? → A: Yes — all four tools return level-specific not-found errors (product, size, and flavour).
- Q: What should happen if `infra/` is missing or empty at startup? → A: Fail fast — server refuses to start and prints a clear diagnostic error.

### Session 2026-05-26

- Q: What MCP transport should the server use? → A: HTTP / SSE — server runs as a persistent HTTP service; Cursor connects via URL.
- Q: How should the MCP server be integrated into the backend? → A: Same process — the MCP endpoint is mounted into the existing web editor backend (one process, automatically available when the backend starts).
- Q: What tool granularity should the MCP server expose? → A: Four tools with a clear hierarchy: (1) list all products, (2) list sizes for a product, (3) list flavours for a size, (4) get full spec for a flavour.
- Q: Should the server pick up infra file changes without a restart? → A: Yes — files are read fresh on every request; changes take effect immediately with no restart needed.
- Q: Where should the Cursor integration documentation live? → A: `docs/mcp-server/` — a new subdirectory following the existing `docs/` pattern.

## Assumptions

- The MCP server will be co-located with the existing web editor backend and share its runtime environment.
- The server reads sizing data directly from the `infra/` directory at query time (no caching layer required for v1).
- Authentication and access control for the MCP endpoint are out of scope; the server is intended for local/internal use.
- The `infra/` directory structure (products.json, per-product sizes.json, per-size component directories) is stable and will not change as part of this feature.
- Documentation targets Cursor as the primary MCP client but the server itself is client-agnostic.
- The existing web editor backend's deployment mechanism (Docker, local dev) will also serve the MCP endpoint.

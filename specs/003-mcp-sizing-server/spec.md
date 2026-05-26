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

1. **Given** the MCP server is running and a product/size combination exists, **When** a client requests sizing data for that combination, **Then** the server returns the complete component specifications for that tier.
2. **Given** a client requests data for a non-existent product or size, **When** the server processes the request, **Then** the server returns a clear error indicating the product or size was not found.
3. **Given** the MCP server is running, **When** a client asks for available products, **Then** the server returns the full list of registered products with their display names.

---

### User Story 2 - Discover Available Products and Sizes (Priority: P2)

A developer wants to know which products and sizing tiers are available in the repository before querying details. They can ask their AI assistant "What products are available?" or "What sizes does ACME ERP come in?" and get an accurate answer.

**Why this priority**: Discovery is essential before querying details; without it, users would need to know product names and sizes in advance, greatly limiting the assistant's usefulness.

**Independent Test**: Can be fully tested by invoking the list-products and list-sizes tools and verifying the response matches the current `products.json` and per-product `sizes.json` files.

**Acceptance Scenarios**:

1. **Given** the MCP server is running, **When** a client requests all available products, **Then** the server returns a list of all products with their short names and display names.
2. **Given** a valid product short name, **When** a client requests available sizes for that product, **Then** the server returns all size tiers defined for that product.
3. **Given** an invalid product short name, **When** a client requests sizes for it, **Then** the server returns an appropriate not-found response.

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

- What happens when the `infra/` directory is missing or empty at server startup?
- How does the server behave when a `sizes.json` file references a size directory that does not exist on disk?
- What happens when the server is queried while the underlying data files are being edited?
- How does the server handle requests for component-level detail when no component JSON files are present in a size directory?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The server MUST expose a tool to list all available products from the infrastructure repository.
- **FR-002**: The server MUST expose a tool to list all available size tiers for a given product.
- **FR-003**: The server MUST expose a tool to retrieve the full sizing specification for a given product and size tier, including all component details.
- **FR-004**: The server MUST return structured, machine-readable responses suitable for AI assistant consumption.
- **FR-005**: The server MUST return meaningful error messages when a requested product or size does not exist.
- **FR-006**: The server MUST read sizing data from the existing `infra/` directory structure without requiring data migration or duplication.
- **FR-007**: The server MUST be integrated into the existing backend component of the web editor.
- **FR-008**: The documentation MUST describe how to add the MCP server as a tool source in Cursor, including connection URL/configuration, and a verification step confirming the connection works.
- **FR-009**: The documentation MUST include a troubleshooting section covering the most common connection and configuration issues.

### Key Entities

- **Product**: A software product available for sizing (e.g., "ACME CRM Platform"), identified by a short name and human-readable display name.
- **Size Tier**: A deployment scale for a product (e.g., "Small – 100 Users"), identified by a short name within its product.
- **Component Group**: A category of infrastructure components within a size tier (e.g., "Application Servers", "Database Servers").
- **Sizing Specification**: The aggregate of all component groups and their configurations for a specific product/size combination.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can retrieve complete sizing data for any valid product/size combination in under 2 seconds via the MCP server.
- **SC-002**: All products and sizes defined in the repository are discoverable through the MCP server without any manual configuration.
- **SC-003**: A developer with no prior knowledge of the project can connect Cursor to the MCP server and make a successful query by following the documentation alone, in under 10 minutes.
- **SC-004**: The MCP server returns a clear, actionable error message for 100% of invalid product or size requests.

## Assumptions

- The MCP server will be co-located with the existing web editor backend and share its runtime environment.
- The server reads sizing data directly from the `infra/` directory at query time (no caching layer required for v1).
- Authentication and access control for the MCP endpoint are out of scope; the server is intended for local/internal use.
- The `infra/` directory structure (products.json, per-product sizes.json, per-size component directories) is stable and will not change as part of this feature.
- Documentation targets Cursor as the primary MCP client but the server itself is client-agnostic.
- The existing web editor backend's deployment mechanism (Docker, local dev) will also serve the MCP endpoint.

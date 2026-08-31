# ADR-014: Local Model Context Protocol (MCP) Boundary using stdio Transport

## Status

Accepted for `v0.7`.

## Context

In milestones `v0.1` through `v0.6`, agent tool calling was handled via in-process Python abstractions and direct function schemas. To standardize tool interfaces according to open, interoperable agent architectures (as emphasized in Microsoft AI-103 and industry practices), `v0.7` introduces the **Model Context Protocol (MCP)**.

For local development and testing:
- Running HTTP servers introduces port collisions, local network security surfaces, and additional lifecycle management.
- The standard MCP specification defines `stdio` as the canonical local transport mechanism.
- The official Python MCP SDK (`mcp>=2.1.1`, implementing MCP Protocol `2026-07-28`) is adopted.

## Decision

1. **Protocol and Transport**:
   - Adopt the official Python `mcp` SDK (`mcp.server.mcpserver.MCPServer`).
   - Use standard `stdio` transport for process-isolated local execution.
   - Negotiate and enforce MCP protocol version `2026-07-28`.

2. **Tool Categorization and Metadata**:
   - Annotate tools strictly according to their semantics:
     - Read tools (`search_knowledge`, `get_my_loans`, `get_loan_details`, `get_next_installment`): `read_only_hint=True`.
     - Write tool (`create_service_request`): `read_only_hint=False`, `destructive_hint=False`.
   - Tool annotations serve as informative metadata; deterministic authorization remains enforced by runtime code and HITL verification.

3. **Structured Error Handling**:
   - MCP tool responses sanitize outputs and wrap errors in deterministic JSON envelopes (`{"success": False, "error": "..."}`) without leaking internal tracebacks, paths, or secrets.

## Consequences

### Positive
- Interoperable standard interface aligned with MCP specification.
- Zero local port conflicts or socket listeners required on the developer workstation.
- Smooth forward migration path to Streamable HTTP when containerized deployment begins in later milestones.

### Negative
- Asynchronous stdio communication requires structured process lifecycle management in testing harnesses.

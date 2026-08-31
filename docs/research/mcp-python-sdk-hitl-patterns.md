# MCP Python SDK HITL (Elicitation) Patterns

Source: <https://py.sdk.modelcontextprotocol.io/handlers/elicitation/> (verified 2026-08-21).

## What elicitation is

A tool that is halfway through its job and missing one answer does not
have to fail. **Elicitation** lets the tool ask the user mid-call, and
the answer flows back into the same function call.

Two modes:

- **Form mode**: the tool needs a value (a confirmation, a date, a
  quantity). The tool describes the fields and the client renders a form.
- **URL mode**: the tool needs the user to go somewhere else (OAuth
  consent, payment). Nothing they do there passes through the protocol.

Two ways to ask:

- **Resolver** (recommended): annotate a parameter
  `Annotated[T, Resolve(fn)]` and the SDK asks for it. Works on any
  connection regardless of protocol era.
- **Direct**: `await ctx.elicit(...)`. Only on legacy connections
  (spec version 2025-11-25 or earlier).

## Resolver pattern (recommended)

```python
from typing import Annotated
from pydantic import BaseModel

from mcp.server import MCPServer
from mcp.server.mcpserver import (
    AcceptedElicitation,
    CancelledElicitation,
    DeclinedElicitation,
    Elicit,
    ElicitationResult,
    Resolve,
)

mcp = MCPServer("Files")


class Confirm(BaseModel):
    ok: bool


async def confirm_delete(path: str) -> Confirm | Elicit[Confirm]:
    file_count = len(_FOLDERS.get(path, []))
    if file_count == 0:
        return Confirm(ok=True)  # no round-trip
    return Elicit(f"{path} has {file_count} file(s). Delete anyway?", Confirm)


@mcp.tool()
async def delete_folder(
    path: str,
    confirm: Annotated[ElicitationResult[Confirm], Resolve(confirm_delete)],
) -> str:
    match confirm:
        case AcceptedElicitation(data=Confirm(ok=True)):
            _FOLDERS.pop(path, None)
            return f"deleted {path}"
        case AcceptedElicitation():
            return "kept the folder"
        case DeclinedElicitation():
            return "declined: folder not deleted"
        case CancelledElicitation():
            return "cancelled: folder not deleted"
```

The resolver reads the tool's `path` argument by name and only elicits
when it must. An empty folder resolves to `Confirm(ok=True)` with zero
round-trips.

## Three possible answers

The framework matches every case explicitly:

- `AcceptedElicitation(data=...)`: user accepted; field is filled.
- `DeclinedElicitation`: user declined.
- `CancelledElicitation`: user cancelled the form.

A wrapped `ElicitationResult[T]` carries the full outcome. Annotate the
unwrapped model (`Annotated[Confirm, Resolve(fn)]`) when the tool does
not need to branch: it receives the model on accept and the call aborts
with an error on decline or cancel.

## URL mode

For human-in-the-loop flows where the user must leave the conversation
(OAuth, payments), the tool can ask the client to open a URL:

```python
@mcp.tool()
async def link_account(provider: str) -> str:
    url = await ctx.elicit_url(f"Open {provider} to grant access")
    return f"open: {url}"
```

URL mode does not return any data through the protocol — the user
finishes the flow out of band.

## Implications for AegisBank

Every state-changing operation in our platform already requires HITL
through the OpenCode proposal gate (see `AGENTS.md`). If/when we ship
a Python (mcp) tool surface, we should:

1. Default to **resolvers**, not direct `ctx.elicit`, so the wiring is
   independent of the negotiated protocol era.
2. Match `AcceptedElicitation`, `DeclinedElicitation`, and
   `CancelledElicitation` explicitly. An unhandled case must never
   silently fall through to a write.
3. Reserve URL mode for OAuth-style consent that already runs through a
   separate UI; otherwise keep approval local to the OpenCode TUI.

Deterministic identity, policy, authorization, validation, and the
audit log stay in the AegisBank service. Elicitation only answers
"is the user present and consenting", not "is the write allowed".

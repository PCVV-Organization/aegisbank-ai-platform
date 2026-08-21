# Pydantic AI + MCP Integration

Source: <https://ai.pydantic.dev/mcp/> (verified 2026-08-21).

## Summary

Pydantic AI supports MCP in two roles:

1. **As a client**: agents connect to MCP servers and use their tools.
2. **As a server**: Pydantic AI agents run inside MCP servers.

## Recommended: the `MCP` capability (v0.x+)

`MCPToolset` (the client wrapper around `fastmcp.Client`) accepts a URL
(Streamable HTTP, SSE), a path to a stdio script, a `fastmcp.Transport`,
a pre-built `fastmcp.Client`, or an in-process `FastMCP` server.

Install with the optional `mcp` group:

```bash
pip install "pydantic-ai-slim[mcp]"
# or
uv add "pydantic-ai-slim[mcp]"
```

Minimal client example:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset

toolset = MCPToolset('http://localhost:8000/mcp')
agent = Agent('openai:gpt-5.2', toolsets=[toolset])

async def main():
    result = await agent.run('What is 7 plus 5?')
```

Recommended: declare a toolset via the `toolsets=[...]` argument and use
`async with agent` so that connections open and close around the run.
Each `MCPToolset` instance is a single identity — for multi-user setups
see **per-user authentication** in the docs.

## Transports supported

- Streamable HTTP (recommended for remote servers).
- HTTP + SSE (deprecated; use Streamable HTTP for new deployments).
- Stdio (subprocess: `StdioTransport`).
- In-process `FastMCP` (testing, no network).

## Server side

`FastMCP` exposes a Pydantic AI agent as an MCP tool:

```python
from mcp.server.fastmcp import FastMCP
from pydantic_ai import Agent

server = FastMCP('Pydantic AI Server')
server_agent = Agent('anthropic:claude-haiku-4-5', instructions='always reply in rhyme')

@server.tool()
async def poet(theme: str) -> str:
    r = await server_agent.run(f'write a poem about {theme}')
    return r.output

if __name__ == '__main__':
    server.run()
```

`MCPSamplingModel` lets the agent sample (call back) through the MCP
client instead of using a direct LLM connection — useful for HITL flows.

## Implications for AegisBank

When we eventually introduce Python (pydantic-ai) agents in v0.5+, the
canonical wiring is `MCPToolset` over stdio to the same MCP servers we
already run from Node — `sequential-thinking`, `filesystem`, `git`. The
HTTP transport is the right shape once these tools face a remote runner.
HITL approval still flows through OpenCode's proposal gate, not through
the MCP server directly; we keep deterministic identity, policy, and
authorization in our own service.

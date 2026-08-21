// E2E smoke for the 4 MCP servers wired in opencode.json.
// Connects via @modelcontextprotocol/sdk (already in .opencode/node_modules).
// Lists tools from each server. Captures stdout/stderr to evidence files.

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const root = "C:/aegisbank-ai-platform";
const evidenceDir = join(root, ".intelligence", "smoke");
mkdirSync(evidenceDir, { recursive: true });

const servers = [
  {
    name: "sequential-thinking",
    command: "node",
    args: [
      "C:/aegisbank-ai-platform/.opencode/node_modules/@modelcontextprotocol/server-sequential-thinking/dist/index.js",
    ],
  },
  {
    name: "filesystem",
    command: "node",
    args: [
      "C:/aegisbank-ai-platform/.opencode/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js",
      "C:/aegisbank-ai-platform",
    ],
  },
  {
    name: "git",
    command: "node",
    args: [
      "C:/aegisbank-ai-platform/.opencode/node_modules/@cyanheads/git-mcp-server/dist/index.js",
    ],
    env: { GIT_MCP_REPO_PATH: "C:/aegisbank-ai-platform" },
  },
  {
    name: "everything",
    command: "node",
    args: [
      "C:/aegisbank-ai-platform/.opencode/node_modules/@modelcontextprotocol/server-everything/dist/index.js",
    ],
  },
  {
    name: "context7",
    command: "node",
    args: [
      "C:/aegisbank-ai-platform/.opencode/node_modules/@upstash/context7-mcp/dist/index.js",
    ],
    env: {
      CONTEXT7_API_KEY:
        process.env.CONTEXT7_API_KEY ?? "ctx7sk-PLACEHOLDER-ROTATE-AT-DASHBOARD",
    },
  },
];

const results = [];

for (const srv of servers) {
  const start = Date.now();
  const transport = new StdioClientTransport({
    command: srv.command,
    args: srv.args,
    env: { ...process.env, ...(srv.env ?? {}) },
    stderr: "pipe",
  });

  const stderrChunks = [];
  if (transport.stderr) {
    transport.stderr.on("data", (chunk) =>
      stderrChunks.push(chunk.toString("utf8")),
    );
  }

  const client = new Client(
    { name: "aegisbank-smoke", version: "0.1.0" },
    { capabilities: {} },
  );

  try {
    await client.connect(transport, { timeout: 10000 });
    const initMs = Date.now() - start;

    const tools = await client.listTools({}, { timeout: 5000 });
    const listMs = Date.now() - start - initMs;

    results.push({
      name: srv.name,
      ok: true,
      serverInfo: {
        name: client.getServerVersion()?.name,
        version: client.getServerVersion()?.version,
        protocolVersion: client.getServerCapabilities()
          ? "(connected)"
          : "(unknown)",
      },
      toolCount: tools.tools?.length ?? 0,
      toolNames: (tools.tools ?? []).map((t) => t.name),
      initMs,
      listMs,
    });

    await client.close();
  } catch (err) {
    results.push({
      name: srv.name,
      ok: false,
      error: String(err?.message ?? err),
      stderr: stderrChunks.join("").slice(-2000),
    });
  }
}

const out = {
  generated_at: new Date().toISOString(),
  opencodeProfile: "minimax-plus",
  results,
  summary: {
    total: results.length,
    ok: results.filter((r) => r.ok).length,
    failed: results.filter((r) => !r.ok).length,
    totalTools: results.reduce((sum, r) => sum + (r.toolCount ?? 0), 0),
  },
};

const jsonPath = join(evidenceDir, "mcp-smoke.json");
writeFileSync(jsonPath, JSON.stringify(out, null, 2));
console.log(`smoke evidence: ${jsonPath}`);
console.log(JSON.stringify(out, null, 2));

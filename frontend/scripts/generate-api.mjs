import { mkdir, writeFile } from "node:fs/promises";

const source = process.env.VITE_OPENAPI_URL;
if (!source) {
  console.error(
    "VITE_OPENAPI_URL is required to regenerate the client from a real OpenAPI document.",
  );
  console.error(
    "The checked-in contract schema is a JSON Schema for validating OpenAPI, not an OpenAPI document.",
  );
  process.exit(1);
}

await mkdir("src/api/generated", { recursive: true });
await writeFile("src/api/generated/.openapi-source", `${source}\n`, "utf8");
console.log(`OpenAPI source recorded: ${source}`);

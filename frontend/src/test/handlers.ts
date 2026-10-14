import { http, HttpResponse } from "msw";

export const handlers = [
  http.post("*/api/v1/agent/run", async () =>
    HttpResponse.json({ answer: "Synthetic response." }),
  ),
];

import { describe, expect, it, vi } from "vitest";
import { apiFetch } from "./transport";

describe("apiFetch", () => {
  it("propagates an AbortSignal", async () => {
    const controller = new AbortController();
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new DOMException("Aborted", "AbortError"));
    const request = apiFetch("/slow", { signal: controller.signal });
    controller.abort();
    await expect(request).rejects.toMatchObject({ name: "AbortError" });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/slow"),
      expect.objectContaining({ signal: controller.signal }),
    );
    fetchMock.mockRestore();
  });
});

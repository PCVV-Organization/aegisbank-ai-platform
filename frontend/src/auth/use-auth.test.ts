import { describe, expect, it } from "vitest";
import { useAuth } from "./use-auth";

describe("mock authentication", () => {
  it("starts with a synthetic user by default", () => {
    expect(useAuth.getState().user?.id).toBe("CUST-0001");
  });
  it("clears the user on sign out", () => {
    useAuth.getState().signOut();
    expect(useAuth.getState().user).toBeNull();
    useAuth.getState().signIn();
  });
});

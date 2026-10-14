import { useSyncExternalStore } from "react";

type User = { id: string; name: string };
type AuthState = { user: User | null; signIn: () => void; signOut: () => void };
let state: AuthState = {
  user:
    import.meta.env.VITE_USE_MOCK_AUTH !== "false"
      ? { id: "CUST-0001", name: "Synthetic customer" }
      : null,
  signIn: () => undefined,
  signOut: () => undefined,
};
const listeners = new Set<() => void>();
state.signIn = () => {
  state = { ...state, user: { id: "CUST-0001", name: "Synthetic customer" } };
  listeners.forEach((listener) => listener());
};
state.signOut = () => {
  state = { ...state, user: null };
  listeners.forEach((listener) => listener());
};

export const useAuth = Object.assign(
  function useAuthHook() {
    return useSyncExternalStore(
      (listener) => {
        listeners.add(listener);
        return () => listeners.delete(listener);
      },
      () => state,
      () => state,
    );
  },
  { getState: () => state },
);

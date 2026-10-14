import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "../../api/transport";

export function useAssistantRun() {
  return useMutation({
    mutationFn: (message: string) =>
      apiFetch<{ answer: string }>("/api/v1/agent/run", {
        method: "POST",
        body: JSON.stringify({ message, customer_id: "CUST-0001" }),
      }),
  });
}

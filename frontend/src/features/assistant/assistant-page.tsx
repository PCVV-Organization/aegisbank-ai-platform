import { useState } from "react";
import { useAssistantRun } from "./use-assistant-run";

export function AssistantPage() {
  const [message, setMessage] = useState("");
  const run = useAssistantRun();
  return (
    <section className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-semibold text-[#0f2747]">Aegis assistant</h1>
      <p className="mt-2 text-slate-600">
        Ask about your synthetic banking information. State-changing actions
        always require approval.
      </p>
      <div
        className="mt-6 min-h-64 rounded-xl bg-white p-5 shadow-sm"
        aria-live="polite"
      >
        {run.data ? (
          <p>{run.data.answer}</p>
        ) : (
          <p className="text-slate-500">No messages yet.</p>
        )}
      </div>
      <form
        className="mt-4 flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          if (message.trim()) {
            run.mutate(message.trim());
            setMessage("");
          }
        }}
      >
        <label className="sr-only" htmlFor="assistant-message">
          Message
        </label>
        <input
          id="assistant-message"
          className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-3"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask a question"
        />
        <button
          className="rounded-lg bg-[#0f2747] px-4 py-3 text-white disabled:opacity-50"
          disabled={run.isPending}
        >
          Send
        </button>
      </form>
      {run.error ? (
        <p role="alert" className="mt-2 text-red-700">
          Unable to reach the assistant.
        </p>
      ) : null}
    </section>
  );
}

import { useForm } from "@tanstack/react-form";
import { z } from "zod";

const requestSchema = z.object({
  summary: z.string().trim().min(5, "Use at least five characters").max(240),
});

export function ServiceRequestForm() {
  const form = useForm({
    defaultValues: { summary: "" },
    validators: { onChange: requestSchema },
    onSubmit: async ({ value }) => {
      requestSchema.parse(value);
    },
  });
  return (
    <form
      className="mt-6 max-w-xl rounded-xl bg-white p-5 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        event.stopPropagation();
        void form.handleSubmit();
      }}
    >
      <form.Field name="summary">
        {(field) => (
          <div>
            <label className="mb-2 block font-medium" htmlFor={field.name}>
              Request summary
            </label>
            <textarea
              id={field.name}
              className="min-h-28 w-full rounded-lg border border-slate-300 p-3"
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(event) => field.handleChange(event.target.value)}
              aria-describedby={`${field.name}-error`}
            />
            {field.state.meta.errors.length > 0 ? (
              <p
                id={`${field.name}-error`}
                className="mt-2 text-sm text-red-700"
                role="alert"
              >
                {field.state.meta.errors.join(", ")}
              </p>
            ) : null}
          </div>
        )}
      </form.Field>
      <form.Subscribe
        selector={(state) => [state.canSubmit, state.isSubmitting]}
      >
        {([canSubmit, isSubmitting]) => (
          <button
            className="mt-4 rounded-lg bg-[#0f2747] px-4 py-3 text-white disabled:opacity-50"
            type="submit"
            disabled={!canSubmit}
          >
            {isSubmitting ? "Saving…" : "Prepare request"}
          </button>
        )}
      </form.Subscribe>
    </form>
  );
}

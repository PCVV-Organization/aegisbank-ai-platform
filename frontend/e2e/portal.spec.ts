import { expect, test } from "@playwright/test";

test("synthetic customer can open the assistant", async ({ page }) => {
  await page.goto("/app/overview");
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();
  await page.getByRole("link", { name: "Assistant" }).click();
  await expect(
    page.getByRole("heading", { name: "Aegis assistant" }),
  ).toBeVisible();
});

test("portal has no serious accessibility violations @a11y", async ({
  page,
}) => {
  await page.goto("/app/overview");
  const { AxeBuilder } = await import("@axe-core/playwright");
  const results = await new AxeBuilder({ page }).analyze();
  expect(
    results.violations.filter((violation) =>
      ["critical", "serious"].includes(violation.impact ?? ""),
    ),
  ).toHaveLength(0);
});

import { expect, test } from "@playwright/test";

test("shows the v3 scan workspace", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Wat wil je vandaag opruimen?" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Start scan" })).toBeVisible();
});

test("shows editable filters for a custom scan", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByLabel("Minimale grootte (MB)")) .toHaveValue("100");
  await expect(page.getByLabel("Minimale ouderdom (dagen)")) .toHaveValue("30");
  await expect(page.getByLabel("Maximale resultaten")) .toHaveValue("100");
});

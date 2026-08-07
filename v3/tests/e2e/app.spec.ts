import { expect, test } from "@playwright/test";

test("shows the v3 scan workspace", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Wat wil je vandaag opruimen?" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Start scan" })).toBeVisible();
});

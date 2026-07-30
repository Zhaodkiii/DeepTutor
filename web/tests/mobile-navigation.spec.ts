import { expect, test } from "@playwright/test";

test.describe("mobile navigation", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("renders bottom tabs and opens control drawer", async ({ page }) => {
    await page.goto("/home");

    await expect(
      page.getByRole("navigation", { name: "Mobile primary navigation" }),
    ).toBeVisible();

    await page.getByRole("button", { name: "Open control panel" }).click();
    await expect(
      page.getByRole("dialog", { name: "Mobile control panel" }),
    ).toBeVisible();

    await page.getByRole("link", { name: "Knowledge Center" }).click();
    await expect(page).toHaveURL(/\/knowledge/);
  });
});

test.describe("desktop navigation", () => {
  test.use({ viewport: { width: 1280, height: 800 } });

  test("keeps desktop sidebar and hides mobile controls", async ({ page }) => {
    await page.goto("/home");

    await expect(
      page.getByRole("navigation", { name: "Mobile primary navigation" }),
    ).toBeHidden();

    await expect(
      page.getByRole("button", { name: "Open control panel" }),
    ).toBeHidden();
  });
});

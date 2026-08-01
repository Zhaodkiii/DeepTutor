import { expect, test } from "@playwright/test";

const MOBILE_VIEWPORTS = [
  { width: 375, height: 812 },
  { width: 390, height: 844 },
  { width: 430, height: 932 },
  { width: 767, height: 900 },
];

test.describe("mobile home layout", () => {
  for (const viewport of MOBILE_VIEWPORTS) {
    test(`does not overflow horizontally at ${viewport.width}px`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport);
      await page.goto("/home");

      const hasOverflow = await page.evaluate(() => {
        return document.documentElement.scrollWidth > window.innerWidth;
      });

      expect(hasOverflow).toBe(false);
    });
  }

  test("mounts only one home page instance on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/home");

    await expect(page.locator("[data-home-page-root='true']")).toHaveCount(1);
  });

  test("keeps composer above mobile bottom tabs", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/home");

    const nav = page.getByRole("navigation", {
      name: "Mobile primary navigation",
    });
    const composer = page.locator("[data-chat-composer='true']");

    await expect(nav).toBeVisible();
    await expect(composer).toBeVisible();

    const navBox = await nav.boundingBox();
    const composerBox = await composer.boundingBox();

    expect(navBox).not.toBeNull();
    expect(composerBox).not.toBeNull();
    expect(composerBox!.y + composerBox!.height).toBeLessThanOrEqual(navBox!.y);
  });

  test("opens control drawer with aria-modal", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/home");

    await page.getByRole("button", { name: "Open control panel" }).click();

    const drawer = page.getByRole("dialog", { name: "Mobile control panel" });
    await expect(drawer).toBeVisible();
    await expect(drawer).toHaveAttribute("aria-modal", "true");

    await page.keyboard.press("Escape");
    await expect(drawer).toBeHidden();
  });

  test("activity panel does not squeeze chat below 320px on mobile", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto("/home");

    const activityButton = page.getByRole("button", { name: "Activity" });
    await expect(activityButton).toBeVisible();
    await activityButton.click();

    const chatShell = page.locator("[data-home-page-root='true']");
    await expect(chatShell).toHaveAttribute("data-viewer-open", "true");

    const chatWidth = await chatShell.evaluate((el) => el.clientWidth);
    expect(chatWidth).toBeGreaterThanOrEqual(320);
  });
});

test.describe("desktop home layout at breakpoint", () => {
  test("mounts only one home page instance at 768px", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 900 });
    await page.goto("/home");

    await expect(page.locator("[data-home-page-root='true']")).toHaveCount(1);
    await expect(
      page.getByRole("navigation", { name: "Mobile primary navigation" }),
    ).toBeHidden();
  });
});

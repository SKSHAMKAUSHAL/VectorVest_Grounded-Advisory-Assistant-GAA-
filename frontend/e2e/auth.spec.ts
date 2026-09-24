import { test, expect } from "@playwright/test";

test.describe("GAA Authentication Module E2E Test Suite", () => {
  const BASE_URL = process.env.PLAYWRIGHT_TEST_BASE_URL || "http://localhost:3000";

  test("1. User Sign Up Flow: Successful registration redirects to dashboard", async ({ page }) => {
    await page.goto(`${BASE_URL}/signup`);

    // Ensure we are on the signup tab
    await expect(page.getByRole("heading", { name: "Create Advisor Account" })).toBeVisible();

    // Fill form fields
    const testEmail = `advisor.${Date.now()}@wealth.bank.com`;
    await page.locator("#signup-name").fill("Alexander Wright");
    await page.locator("#signup-email").fill(testEmail);
    await page.locator("#signup-password").fill("StrongPass2024!");
    await page.locator("#signup-confirm-password").fill("StrongPass2024!");

    // Verify password strength indicator reflects strong
    await expect(page.locator("#signup-password-hint")).toContainText("Strong");

    // Accept terms & conditions
    await page.locator("#terms-accepted").check();

    // Submit form
    await page.getByRole("button", { name: /create account/i }).click();

    // Verify redirection to root dashboard
    await page.waitForURL(`${BASE_URL}/`, { timeout: 10000 });
    expect(page.url()).toBe(`${BASE_URL}/`);

    // Verify token stored in localStorage
    const token = await page.evaluate(() => localStorage.getItem("gaa_token"));
    expect(token).toBeTruthy();
  });

  test("2. User Sign In Flow: Valid credentials redirects and hydrates session", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await expect(page.getByRole("heading", { name: "Sign In to Advisory Terminal" })).toBeVisible();

    // Input verified demo RM credentials
    await page.locator("#signin-email").fill("rm@wealth.bank.com");
    await page.locator("#signin-password").fill("AdvisoryPass2024!");

    // Toggle password visibility
    const toggleBtn = page.getByLabel("Show password");
    if (await toggleBtn.isVisible()) {
      await toggleBtn.click();
      await expect(page.locator("#signin-password")).toHaveAttribute("type", "text");
      await page.getByLabel("Hide password").click();
      await expect(page.locator("#signin-password")).toHaveAttribute("type", "password");
    }

    // Submit Sign In
    await page.getByRole("button", { name: /sign in/i }).click();

    // Verify redirection to dashboard
    await page.waitForURL(`${BASE_URL}/`, { timeout: 10000 });
    expect(page.url()).toBe(`${BASE_URL}/`);

    // Verify token stored in localStorage
    const token = await page.evaluate(() => localStorage.getItem("gaa_token"));
    expect(token).toBeTruthy();
  });

  test("3. Invalid Credentials Flow: Shows error banner with expected message", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await page.locator("#signin-email").fill("rm@wealth.bank.com");
    await page.locator("#signin-password").fill("WrongPassword999!");

    await page.getByRole("button", { name: /sign in/i }).click();

    // Verify error banner appears
    const errorBanner = page.getByRole("alert");
    await expect(errorBanner).toBeVisible({ timeout: 5000 });
    await expect(errorBanner).toContainText("Incorrect email or password");
  });

  test("4. Form Validation Checks: Empty submit displays inline error messages", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Attempt to submit empty form
    await page.getByRole("button", { name: /sign in/i }).click();

    // Check for validation error messages
    await expect(page.locator("#signin-email-error")).toBeVisible();
    await expect(page.locator("#signin-email-error")).toContainText("Email address is required");
  });
});

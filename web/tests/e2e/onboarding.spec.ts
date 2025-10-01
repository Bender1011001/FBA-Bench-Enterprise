import { test, expect } from "@playwright/test";

// Basic onboarding flow visiting baseURL, registering, and landing on dashboard.
test("user can register and see dashboard", async ({ page }) => {
  // Navigate to the app root (baseURL is set in playwright.config.ts)
  await page.goto("/");

  // Open registration
  const registerLink = page.getByRole("link", { name: /register|sign up|create account/i });
  if (await registerLink.isVisible()) {
    await registerLink.click();
  } else {
    // Fallback: try a button if link not found
    const registerButton = page.getByRole("button", { name: /register|sign up|create account/i });
    await registerButton.click();
  }

  // Fill credentials
  await page.getByLabel(/email/i).fill(`e2e.user+${Date.now()}@example.com`);
  await page.getByLabel(/password/i).fill("Str0ngP@ssw0rd!");

  // Submit
  const submit = page.getByRole("button", { name: /register|sign up|create account|continue/i });
  await submit.click();

  // Assert dashboard visible
  await expect(page).toHaveURL(/dashboard/i);
  await expect(page.getByRole("heading", { name: /dashboard/i })).toBeVisible();
});
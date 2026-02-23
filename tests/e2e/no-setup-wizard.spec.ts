import { test, expect } from "@playwright/test"

test.describe("First Load Experience", () => {
	test("redirects to demo project page, not setup wizard", async ({ page }) => {
		await page.goto("/")
		// Should redirect to demo project page
		await expect(page).toHaveURL(/\/projects\//)
		// Demo project name visible
		await expect(page.getByText("GeoStorm Demo: FastAPI")).toBeVisible()
	})

	test("shows demo banner with API key link", async ({ page }) => {
		await page.goto("/")
		await expect(page.getByText("read-only demo project")).toBeVisible()
		await expect(page.getByText("Add your OpenRouter API key")).toBeVisible()
	})

	test("does not show setup wizard or welcome text", async ({ page }) => {
		await page.goto("/")
		await expect(page.getByText("GeoStorm Demo: FastAPI")).toBeVisible()
		await expect(page.getByText("Setup Wizard")).not.toBeVisible()
		await expect(page.getByText("Welcome to GeoStorm")).not.toBeVisible()
	})
})

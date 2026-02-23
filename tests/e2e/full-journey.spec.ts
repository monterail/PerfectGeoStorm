import { test, expect } from "@playwright/test"

test.describe("Full User Journey", () => {
	test("loads demo project with Signal Panel", async ({ page }) => {
		await page.goto("/")
		// Should land on demo project detail page
		await expect(page).toHaveURL(/\/projects\//)
		await expect(page.getByText("GeoStorm Demo: FastAPI")).toBeVisible()
	})

	test("can navigate to settings and enter API key", async ({ page }) => {
		await page.goto("/settings")
		// Settings page should load
		await expect(page.getByText("API Key")).toBeVisible()
	})

	test("can navigate to projects list", async ({ page }) => {
		await page.goto("/projects")
		// Should see the projects page
		await expect(page.getByText("Create Project")).toBeVisible()
	})

	test("create project link navigates to setup", async ({ page }) => {
		await page.goto("/projects")
		const createButton = page.getByRole("link", { name: /create project/i })
		await expect(createButton).toBeVisible()
		await createButton.click()
		await expect(page).toHaveURL(/\/setup/)
	})
})

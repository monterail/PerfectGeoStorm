import { test, expect } from "@playwright/test"

const DEMO_PROJECT_ID = "demo-fastapi"

test.describe("Demo Project Isolation", () => {
	test("PATCH /api/projects/{id} returns 403 for demo project", async ({ request }) => {
		const response = await request.patch(`/api/projects/${DEMO_PROJECT_ID}`, {
			data: { name: "Hacked" },
		})
		expect(response.status()).toBe(403)
	})

	test("POST /api/projects/{id}/competitors returns 403 for demo project", async ({ request }) => {
		const response = await request.post(`/api/projects/${DEMO_PROJECT_ID}/competitors`, {
			data: { name: "Evil Corp" },
		})
		expect(response.status()).toBe(403)
	})

	test("PATCH /api/projects/{id}/schedule returns 403 for demo project", async ({ request }) => {
		const response = await request.patch(`/api/projects/${DEMO_PROJECT_ID}/schedule`, {
			data: { hour_of_day: 12, days_of_week: [0, 1, 2] },
		})
		expect(response.status()).toBe(403)
	})

	test("POST /api/projects/{id}/terms returns 403 for demo project", async ({ request }) => {
		const response = await request.post(`/api/projects/${DEMO_PROJECT_ID}/terms`, {
			data: { term: "test term" },
		})
		expect(response.status()).toBe(403)
	})

	test("shows demo banner in UI", async ({ page }) => {
		await page.goto("/")
		await expect(page.getByText("read-only demo project")).toBeVisible()
	})
})

import { defineConfig } from "@playwright/test"

export default defineConfig({
	testDir: "../tests/e2e",
	fullyParallel: false,
	workers: 1,
	retries: 0,
	use: {
		baseURL: "http://localhost:8080",
		trace: "on-first-retry",
	},
	projects: [
		{
			name: "chromium",
			use: { browserName: "chromium" },
		},
	],
})

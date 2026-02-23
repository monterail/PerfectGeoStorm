const API_BASE = import.meta.env.PUBLIC_API_URL ?? "/api"

export async function apiFetch<T>(
	path: string,
	options?: RequestInit,
): Promise<T> {
	const response = await fetch(`${API_BASE}${path}`, {
		headers: { "Content-Type": "application/json", ...options?.headers },
		...options,
	})
	if (!response.ok) {
		throw new Error(`API error: ${response.status}`)
	}
	return response.json() as Promise<T>
}

import { useQuery } from "@tanstack/react-query"
import { fetchProjectHeatmap, fetchRunBreakdown } from "@/lib/api"
import { apiFetch } from "@/lib/api"
import type { ProjectHeatmapResponse, Response, Run, RunBreakdownResponse, RunDetail } from "@/schemas/run"
import type { PaginatedResponse } from "@/schemas/shared"

export function useRuns(
	projectId: string,
	options?: { limit?: number; offset?: number; status?: string; enablePolling?: boolean },
) {
	const params = new URLSearchParams()
	if (options?.limit) params.set("limit", String(options.limit))
	if (options?.offset) params.set("offset", String(options.offset))
	if (options?.status) params.set("status", options.status)
	const qs = params.toString()
	return useQuery({
		queryKey: ["runs", projectId, options],
		queryFn: () =>
			apiFetch<PaginatedResponse<Run>>(
				`/projects/${projectId}/runs${qs ? `?${qs}` : ""}`,
			),
		enabled: !!projectId,
		refetchInterval: options?.enablePolling
			? (query) => {
					const data = query.state.data as PaginatedResponse<Run> | undefined
					if (data?.items.some((run) => run.status === "running" || run.status === "pending")) {
						return 3000
					}
					return false
				}
			: undefined,
	})
}

export function useRun(runId: string) {
	return useQuery({
		queryKey: ["runs", "detail", runId],
		queryFn: () => apiFetch<RunDetail>(`/runs/${runId}`),
		enabled: !!runId,
	})
}

export function useRunResponses(
	runId: string,
	options?: { limit?: number; offset?: number },
) {
	const params = new URLSearchParams()
	if (options?.limit) params.set("limit", String(options.limit))
	if (options?.offset) params.set("offset", String(options.offset))
	const qs = params.toString()
	return useQuery({
		queryKey: ["runs", runId, "responses", options],
		queryFn: () =>
			apiFetch<PaginatedResponse<Response>>(
				`/runs/${runId}/responses${qs ? `?${qs}` : ""}`,
			),
		enabled: !!runId,
	})
}

export function useRunBreakdown(runId: string | null, provider?: string) {
	return useQuery<RunBreakdownResponse>({
		queryKey: ["runs", runId, "breakdown", provider],
		queryFn: () => fetchRunBreakdown(runId!, provider),
		enabled: !!runId,
	})
}

export function useProjectHeatmap(projectId: string, provider?: string) {
	return useQuery<ProjectHeatmapResponse>({
		queryKey: ["heatmap", projectId, provider],
		queryFn: () => fetchProjectHeatmap(projectId, provider),
		enabled: !!projectId,
	})
}

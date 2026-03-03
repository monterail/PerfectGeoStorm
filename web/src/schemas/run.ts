import { z } from "zod"

export const RunStatus = z.enum([
	"pending",
	"running",
	"completed",
	"failed",
	"cancelled",
])

export type RunStatus = z.infer<typeof RunStatus>

export const RunSchema = z.object({
	id: z.string(),
	project_id: z.string(),
	status: RunStatus,
	trigger_type: z.enum(["immediate", "scheduled", "manual"]),
	triggered_by: z.string().nullable(),
	total_queries: z.number(),
	completed_queries: z.number(),
	failed_queries: z.number(),
	started_at: z.string().nullable(),
	completed_at: z.string().nullable(),
	created_at: z.string(),
})

export type Run = z.infer<typeof RunSchema>

export const RunDetailSchema = RunSchema.extend({
	perception_score: z.number().nullable(),
	recommendation_share: z.number().nullable(),
	competitors_detected: z.array(z.string()),
})

export type RunDetail = z.infer<typeof RunDetailSchema>

export const MentionSchema = z.object({
	id: z.string(),
	mention_type: z.enum(["brand", "competitor"]),
	target_name: z.string(),
	position_chars: z.number().nullable(),
	position_words: z.number().nullable(),
	list_position: z.number().nullable(),
	context_before: z.string(),
	context_after: z.string(),
})

export type Mention = z.infer<typeof MentionSchema>

export const ResponseSchema = z.object({
	id: z.string(),
	run_id: z.string(),
	term_id: z.string(),
	term_name: z.string(),
	provider_name: z.string(),
	model_name: z.string(),
	response_text: z.string(),
	latency_ms: z.number().nullable(),
	cost_usd: z.number().nullable(),
	error_message: z.string().nullable(),
	created_at: z.string(),
	mentions: z.array(MentionSchema),
})

export type Response = z.infer<typeof ResponseSchema>

export const RunTermBreakdownItemSchema = z.object({
	term_id: z.string(),
	term_name: z.string(),
	total_responses: z.number(),
	brand_mentions: z.number(),
	mention_pct: z.number(),
})

export type RunTermBreakdownItem = z.infer<typeof RunTermBreakdownItemSchema>

export const RunBreakdownResponseSchema = z.object({
	run_id: z.string(),
	provider: z.string().nullable(),
	terms: z.array(RunTermBreakdownItemSchema),
})

export type RunBreakdownResponse = z.infer<typeof RunBreakdownResponseSchema>

export const HeatmapCellSchema = z.object({
	term_id: z.string(),
	term_name: z.string(),
	mention_pct: z.number().nullable(),
})

export type HeatmapCell = z.infer<typeof HeatmapCellSchema>

export const HeatmapRowSchema = z.object({
	run_id: z.string(),
	run_date: z.string(),
	cells: z.array(HeatmapCellSchema),
})

export type HeatmapRow = z.infer<typeof HeatmapRowSchema>

export const ProjectHeatmapResponseSchema = z.object({
	project_id: z.string(),
	provider: z.string().nullable(),
	terms: z.array(z.string()),
	rows: z.array(HeatmapRowSchema),
	available_providers: z.array(z.string()),
})

export type ProjectHeatmapResponse = z.infer<typeof ProjectHeatmapResponseSchema>

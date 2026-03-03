import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useProjectHeatmap } from "@/hooks/useRuns"

interface ProjectHeatmapProps {
	projectId: string
}

function heatColor(pct: number | null): string {
	if (pct === null) return "bg-muted"
	if (pct === 0) return "bg-red-100 dark:bg-red-950"
	if (pct < 0.4) return "bg-orange-100 dark:bg-orange-950"
	if (pct < 0.7) return "bg-yellow-100 dark:bg-yellow-900"
	return "bg-green-100 dark:bg-green-950"
}

function formatDate(dateStr: string): string {
	return new Date(dateStr).toLocaleDateString([], {
		month: "short",
		day: "numeric",
		hour: "numeric",
		minute: "2-digit",
	})
}

function truncate(str: string, maxLen = 20): string {
	return str.length > maxLen ? `${str.slice(0, maxLen)}…` : str
}

export function ProjectHeatmap({ projectId }: ProjectHeatmapProps) {
	const [provider, setProvider] = useState<string | undefined>(undefined)
	const { data, isLoading, error } = useProjectHeatmap(projectId, provider)

	if (isLoading) {
		return (
			<Card>
				<CardHeader>
					<CardTitle className="text-lg">Mention Rate Heatmap</CardTitle>
				</CardHeader>
				<CardContent className="space-y-3">
					{[1, 2, 3].map((i) => (
						<Skeleton key={i} className="h-8 w-full" />
					))}
				</CardContent>
			</Card>
		)
	}

	if (error) {
		return (
			<Card>
				<CardHeader>
					<CardTitle className="text-lg">Mention Rate Heatmap</CardTitle>
				</CardHeader>
				<CardContent>
					<p className="text-sm text-destructive">Failed to load heatmap data.</p>
				</CardContent>
			</Card>
		)
	}

	if (!data || data.rows.length === 0) return null

	const { terms, rows, available_providers } = data

	return (
		<Card>
			<CardHeader>
				<div className="flex items-center justify-between flex-wrap gap-2">
					<CardTitle className="text-lg">Mention Rate Heatmap</CardTitle>
					{available_providers.length > 1 && (
						<div className="flex gap-1 flex-wrap">
							<Button
								size="sm"
								variant={provider === undefined ? "default" : "outline"}
								onClick={() => setProvider(undefined)}
							>
								All
							</Button>
							{available_providers.map((p) => (
								<Button
									key={p}
									size="sm"
									variant={provider === p ? "default" : "outline"}
									onClick={() => setProvider(p)}
								>
									{p}
								</Button>
							))}
						</div>
					)}
				</div>
			</CardHeader>
			<CardContent>
				<div className="overflow-x-auto">
					<table className="text-xs border-collapse">
						<thead>
							<tr>
								<th className="pb-2 pr-3 text-left font-medium text-muted-foreground whitespace-nowrap">
									Run
								</th>
								{terms.map((term) => (
									<th
										key={term}
										className="pb-2 px-2 font-medium text-muted-foreground text-center"
										title={term}
									>
										{truncate(term)}
									</th>
								))}
							</tr>
						</thead>
						<tbody>
							{rows.map((row) => (
								<tr key={row.run_id}>
									<td className="py-1 pr-3 whitespace-nowrap text-muted-foreground">
										{formatDate(row.run_date)}
									</td>
									{row.cells.map((cell) => (
										<td
											key={cell.term_id}
											className={`py-1 px-2 text-center rounded ${heatColor(cell.mention_pct)}`}
											title={`${cell.term_name}: ${cell.mention_pct !== null ? `${Math.round(cell.mention_pct * 100)}%` : "no data"}`}
										>
											{cell.mention_pct !== null
												? `${Math.round(cell.mention_pct * 100)}%`
												: "—"}
										</td>
									))}
								</tr>
							))}
						</tbody>
					</table>
				</div>
				<div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
					<span className="flex items-center gap-1">
						<span className="inline-block h-3 w-3 rounded bg-green-100 dark:bg-green-950" /> ≥70%
					</span>
					<span className="flex items-center gap-1">
						<span className="inline-block h-3 w-3 rounded bg-yellow-100 dark:bg-yellow-900" /> 40–69%
					</span>
					<span className="flex items-center gap-1">
						<span className="inline-block h-3 w-3 rounded bg-orange-100 dark:bg-orange-950" /> 1–39%
					</span>
					<span className="flex items-center gap-1">
						<span className="inline-block h-3 w-3 rounded bg-red-100 dark:bg-red-950" /> 0%
					</span>
				</div>
			</CardContent>
		</Card>
	)
}

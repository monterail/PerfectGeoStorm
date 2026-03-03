import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useRunBreakdown } from "@/hooks/useRuns"

interface RunBreakdownProps {
	runId: string
	provider?: string
}

export function RunBreakdown({ runId, provider }: RunBreakdownProps) {
	const { data, isLoading, error } = useRunBreakdown(runId, provider)

	if (isLoading) {
		return (
			<div className="space-y-3">
				{[1, 2, 3].map((i) => (
					<div key={i} className="flex gap-4">
						<Skeleton className="h-4 w-48" />
						<Skeleton className="h-4 w-12" />
						<Skeleton className="h-4 w-12" />
					</div>
				))}
			</div>
		)
	}

	if (error) {
		return (
			<p className="text-sm text-destructive">Failed to load run summary.</p>
		)
	}

	const terms = data?.terms ?? []

	if (terms.length === 0) {
		return (
			<p className="py-8 text-center text-sm text-muted-foreground">
				No term data for this run.
			</p>
		)
	}

	return (
		<div className="overflow-x-auto">
			<table className="w-full text-sm">
				<thead>
					<tr className="border-b text-left text-muted-foreground">
						<th className="pb-2 pr-4 font-medium">Search Term</th>
						<th className="pb-2 pr-4 font-medium">Mentioned</th>
						<th className="pb-2 font-medium">%</th>
					</tr>
				</thead>
				<tbody>
					{terms.map((term) => {
						const mentioned = term.brand_mentions > 0
						return (
							<tr key={term.term_id} className="border-b last:border-b-0">
								<td className="py-2 pr-4 font-medium">{term.term_name}</td>
								<td className="py-2 pr-4">
									{mentioned ? (
										<Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
											✓
										</Badge>
									) : (
										<Badge variant="secondary" className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
											✗
										</Badge>
									)}
								</td>
								<td className="py-2">
									{Math.round(term.mention_pct * 100)}%
								</td>
							</tr>
						)
					})}
				</tbody>
			</table>
		</div>
	)
}

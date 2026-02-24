import { Button } from "@/components/ui/button"
import { useTriggerMonitoring } from "@/hooks/useProjects"
import { useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"
import { toast } from "sonner"

interface MonitorButtonProps {
	projectId: string
	isDemo?: boolean
}

export function MonitorButton({ projectId, isDemo }: MonitorButtonProps) {
	const mutation = useTriggerMonitoring(projectId)
	const queryClient = useQueryClient()

	useEffect(() => {
		if (mutation.isSuccess) {
			toast.success("Monitoring run started", {
				description: "Results will appear shortly.",
			})
			queryClient.invalidateQueries({ queryKey: ["perception"] })
			queryClient.invalidateQueries({ queryKey: ["alerts", projectId] })
		}
	}, [mutation.isSuccess, queryClient, projectId])

	useEffect(() => {
		if (mutation.isError) {
			const message = mutation.error instanceof Error
				? mutation.error.message
				: "Unknown error"
			toast.error("Monitoring failed", {
				description: message,
			})
		}
	}, [mutation.isError, mutation.error])

	return (
		<Button
			onClick={() => mutation.mutate()}
			disabled={mutation.isPending || isDemo}
		>
			{mutation.isPending ? "Running..." : "Monitor Now"}
		</Button>
	)
}

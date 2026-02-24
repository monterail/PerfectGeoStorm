import { Button } from "@/components/ui/button"
import { useTriggerMonitoring } from "@/hooks/useProjects"
import { useEffect } from "react"

interface MonitorButtonProps {
	projectId: string
	isDemo?: boolean
}

export function MonitorButton({ projectId, isDemo }: MonitorButtonProps) {
	const mutation = useTriggerMonitoring(projectId)

	useEffect(() => {
		if (mutation.isSuccess) {
			window.alert("Monitoring run started.")
		}
	}, [mutation.isSuccess])

	useEffect(() => {
		if (mutation.isError) {
			const message = mutation.error instanceof Error
				? mutation.error.message
				: "Unknown error"
			window.alert(`Monitoring failed: ${message}`)
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

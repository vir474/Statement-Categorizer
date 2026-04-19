import { useQuery } from "@tanstack/react-query";
import { fetchAvailableMonths, fetchBudgetSummary } from "../api";

export function useAvailableMonths() {
  return useQuery({ queryKey: ["budget-months"], queryFn: fetchAvailableMonths });
}

export function useBudgetSummary(month: string | null) {
  return useQuery({
    queryKey: ["budget-summary", month],
    queryFn: () => fetchBudgetSummary(month!),
    enabled: !!month,
  });
}

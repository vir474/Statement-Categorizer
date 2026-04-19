import apiClient from "@/lib/api-client";
import type { BudgetSummary } from "@/types";

export async function fetchBudgetSummary(month: string): Promise<BudgetSummary> {
  const { data } = await apiClient.get("/budgets/summary", { params: { month } });
  return data;
}

export async function fetchAvailableMonths(): Promise<string[]> {
  const { data } = await apiClient.get("/budgets/months");
  return data;
}

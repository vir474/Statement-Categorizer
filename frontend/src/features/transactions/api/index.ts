import apiClient from "@/lib/api-client";
import type { Transaction } from "@/types";

export interface TransactionFilters {
  statement_id?: number;
  category_id?: number;
  uncategorized_only?: boolean;
  month?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export async function fetchTransactions(filters: TransactionFilters = {}): Promise<Transaction[]> {
  const { data } = await apiClient.get("/transactions/", { params: filters });
  return data;
}

export async function updateTransaction(
  id: number,
  body: { category_id?: number | null; merchant?: string }
): Promise<Transaction> {
  const { data } = await apiClient.patch(`/transactions/${id}`, body);
  return data;
}

export async function recategorizeTransactions(ids: number[]): Promise<Transaction[]> {
  const { data } = await apiClient.post("/transactions/recategorize", { transaction_ids: ids });
  return data;
}

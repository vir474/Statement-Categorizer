import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchTransactions, recategorizeTransactions, updateTransaction } from "../api";
import type { TransactionFilters } from "../api";

export const TXN_KEY = (filters: TransactionFilters) => ["transactions", filters];

export function useTransactions(filters: TransactionFilters = {}) {
  return useQuery({
    queryKey: TXN_KEY(filters),
    queryFn: () => fetchTransactions(filters),
  });
}

export function useUpdateTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: { category_id?: number | null } }) =>
      updateTransaction(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["transactions"] }),
  });
}

export function useRecategorize() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: recategorizeTransactions,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["transactions"] }),
  });
}

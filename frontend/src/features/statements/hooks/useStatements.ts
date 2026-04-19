import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { deleteStatement, fetchStatements, updateStatement, uploadStatement } from "../api";

export const STATEMENTS_KEY = ["statements"];

export function useStatements() {
  return useQuery({ queryKey: STATEMENTS_KEY, queryFn: fetchStatements });
}

export function useUploadStatement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: uploadStatement,
    onSuccess: () => qc.invalidateQueries({ queryKey: STATEMENTS_KEY }),
  });
}

export function useUpdateStatement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: { account_name: string } }) =>
      updateStatement(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: STATEMENTS_KEY }),
  });
}

export function useDeleteStatement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteStatement,
    onSuccess: () => qc.invalidateQueries({ queryKey: STATEMENTS_KEY }),
  });
}

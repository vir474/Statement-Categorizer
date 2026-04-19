import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createCategory, createRule, deleteCategory, deleteRule,
  fetchCategories, fetchRules, updateCategory,
} from "../api";

export const CATEGORIES_KEY = ["categories"];

export function useCategories() {
  return useQuery({ queryKey: CATEGORIES_KEY, queryFn: fetchCategories });
}

export function useCreateCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createCategory,
    onSuccess: () => qc.invalidateQueries({ queryKey: CATEGORIES_KEY }),
  });
}

export function useUpdateCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: Parameters<typeof updateCategory>[1] }) =>
      updateCategory(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: CATEGORIES_KEY }),
  });
}

export function useDeleteCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => qc.invalidateQueries({ queryKey: CATEGORIES_KEY }),
  });
}

export function useRules(categoryId: number | null) {
  return useQuery({
    queryKey: ["rules", categoryId],
    queryFn: () => fetchRules(categoryId!),
    enabled: categoryId !== null,
  });
}

export function useCreateRule(categoryId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { pattern: string; is_regex: boolean; priority: number }) =>
      createRule(categoryId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules", categoryId] }),
  });
}

export function useDeleteRule(categoryId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ruleId: number) => deleteRule(categoryId, ruleId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rules", categoryId] }),
  });
}

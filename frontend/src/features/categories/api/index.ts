import apiClient from "@/lib/api-client";
import type { Category, CategoryRule } from "@/types";

export async function fetchCategories(): Promise<Category[]> {
  const { data } = await apiClient.get("/categories/");
  return data;
}

export async function createCategory(body: {
  name: string;
  parent_id?: number | null;
  color?: string;
}): Promise<Category> {
  const { data } = await apiClient.post("/categories/", body);
  return data;
}

export async function updateCategory(
  id: number,
  body: { name?: string; color?: string; parent_id?: number | null }
): Promise<Category> {
  const { data } = await apiClient.patch(`/categories/${id}`, body);
  return data;
}

export async function deleteCategory(id: number): Promise<void> {
  await apiClient.delete(`/categories/${id}`);
}

export async function fetchRules(categoryId: number): Promise<CategoryRule[]> {
  const { data } = await apiClient.get(`/categories/${categoryId}/rules`);
  return data;
}

export async function createRule(
  categoryId: number,
  body: { pattern: string; is_regex: boolean; priority: number }
): Promise<CategoryRule> {
  const { data } = await apiClient.post(`/categories/${categoryId}/rules`, {
    ...body,
    category_id: categoryId,
  });
  return data;
}

export async function deleteRule(categoryId: number, ruleId: number): Promise<void> {
  await apiClient.delete(`/categories/${categoryId}/rules/${ruleId}`);
}

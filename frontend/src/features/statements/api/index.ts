import apiClient from "@/lib/api-client";
import type { Statement } from "@/types";

export async function fetchStatements(): Promise<Statement[]> {
  const { data } = await apiClient.get("/statements/");
  return data;
}

export async function uploadStatement(file: File): Promise<Statement> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post("/statements/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function updateStatement(id: number, body: { account_name?: string }): Promise<Statement> {
  const { data } = await apiClient.patch(`/statements/${id}`, body);
  return data;
}

export async function deleteStatement(id: number): Promise<void> {
  await apiClient.delete(`/statements/${id}`);
}

export async function reparseStatement(id: number): Promise<Statement> {
  const { data } = await apiClient.post(`/statements/${id}/reparse`);
  return data;
}

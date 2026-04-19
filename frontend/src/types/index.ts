/** Shared TypeScript types mirroring backend Pydantic schemas. */

export interface Category {
  id: number;
  name: string;
  parent_id: number | null;
  color: string;
  icon: string;
  is_user_defined: boolean;
  created_at: string;
}

export interface CategoryRule {
  id: number;
  category_id: number;
  pattern: string;
  is_regex: boolean;
  priority: number;
  created_at: string;
}

export interface Statement {
  id: number;
  filename: string;
  file_format: string;
  account_name: string | null;
  period_start: string | null;
  period_end: string | null;
  parse_status: "pending" | "parsing" | "done" | "error";
  parse_error: string | null;
  uploaded_at: string;
  transaction_count: number;
}

export interface Transaction {
  id: number;
  statement_id: number;
  date: string;
  description: string;
  merchant: string | null;
  amount: string;
  currency: string;
  category_id: number | null;
  categorization_source: "rule" | "ollama" | "claude" | "manual" | "uncategorized";
  created_at: string;
}

export interface CategorySpend {
  category_id: number | null;
  category_name: string;
  parent_category_name: string | null;
  total: string;
  transaction_count: number;
}

export interface BudgetSummary {
  month: string;
  total_spend: string;
  total_income: string;
  net: string;
  by_category: CategorySpend[];
}

/**
 * Transactions page — filterable table with inline category editing.
 * Users can change a category directly in the table row via a dropdown.
 */
import { useState } from "react";
import { RefreshCw, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { formatCurrency, formatDate, cn } from "@/lib/utils";
import type { Transaction } from "@/types";
import { useCategories } from "@/features/categories/hooks/useCategories";
import { useTransactions, useUpdateTransaction, useRecategorize } from "../hooks/useTransactions";

const SOURCE_LABELS: Record<string, string> = {
  rule: "Rule",
  ollama: "AI",
  claude: "AI",
  manual: "Manual",
  uncategorized: "—",
};

export function TransactionsPage() {
  const [search, setSearch] = useState("");
  const [month, setMonth] = useState("");
  const [uncategorizedOnly, setUncategorizedOnly] = useState(false);

  const { data: transactions = [], isLoading } = useTransactions({
    search: search || undefined,
    month: month || undefined,
    uncategorized_only: uncategorizedOnly,
    limit: 500,
  });

  const { data: categories = [] } = useCategories();
  const updateTxn = useUpdateTransaction();
  const recategorize = useRecategorize();

  const uncategorizedIds = transactions
    .filter((t) => !t.category_id && t.categorization_source !== "manual")
    .map((t) => t.id);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold">Transactions</h2>
          <p className="text-muted-foreground text-sm">{transactions.length} transactions</p>
        </div>
        {uncategorizedIds.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => recategorize.mutate(uncategorizedIds)}
            disabled={recategorize.isPending}
          >
            <RefreshCw size={14} className={cn("mr-2", recategorize.isPending && "animate-spin")} />
            Re-categorize {uncategorizedIds.length} uncategorized
          </Button>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-2.5 top-2.5 text-muted-foreground" />
          <Input
            placeholder="Search description or merchant…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
        <Input
          type="month"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="w-40"
        />
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={uncategorizedOnly}
            onChange={(e) => setUncategorizedOnly(e.target.checked)}
            className="rounded"
          />
          Uncategorized only
        </label>
      </div>

      {/* Table */}
      {isLoading ? (
        <p className="text-muted-foreground text-sm">Loading…</p>
      ) : (
        <div className="border rounded-lg overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-muted-foreground">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">Date</th>
                <th className="text-left px-4 py-2.5 font-medium">Description</th>
                <th className="text-left px-4 py-2.5 font-medium">Category</th>
                <th className="text-right px-4 py-2.5 font-medium">Amount</th>
                <th className="text-left px-4 py-2.5 font-medium">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {transactions.map((txn) => (
                <TransactionRow
                  key={txn.id}
                  txn={txn}
                  categories={categories}
                  onCategoryChange={(catId) =>
                    updateTxn.mutate({ id: txn.id, body: { category_id: catId } })
                  }
                />
              ))}
            </tbody>
          </table>
          {transactions.length === 0 && (
            <p className="text-center text-muted-foreground py-10 text-sm">
              No transactions found.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function TransactionRow({
  txn,
  categories,
  onCategoryChange,
}: {
  txn: Transaction;
  categories: import("@/types").Category[];
  onCategoryChange: (id: number | null) => void;
}) {
  const amount = parseFloat(txn.amount);
  const isCredit = amount < 0;

  return (
    <tr className="hover:bg-muted/30 transition-colors">
      <td className="px-4 py-2.5 whitespace-nowrap text-muted-foreground">
        {formatDate(txn.date)}
      </td>
      <td className="px-4 py-2.5 max-w-xs">
        <div className="font-medium truncate">{txn.merchant || txn.description}</div>
        {txn.merchant && (
          <div className="text-xs text-muted-foreground truncate">{txn.description}</div>
        )}
      </td>
      <td className="px-4 py-2.5">
        <Select
          value={txn.category_id?.toString() || ""}
          onChange={(e) =>
            onCategoryChange(e.target.value ? parseInt(e.target.value) : null)
          }
          className="h-7 text-xs w-44"
        >
          <option value="">— Uncategorized —</option>
          {/* Group by parent */}
          {categories
            .filter((c) => !c.parent_id)
            .map((parent) => {
              const children = categories.filter((c) => c.parent_id === parent.id);
              return children.length > 0 ? (
                <optgroup key={parent.id} label={parent.name}>
                  {children.map((sub) => (
                    <option key={sub.id} value={sub.id}>{sub.name}</option>
                  ))}
                </optgroup>
              ) : (
                <option key={parent.id} value={parent.id}>{parent.name}</option>
              );
            })}
        </Select>
      </td>
      <td className={cn(
        "px-4 py-2.5 text-right font-mono font-medium whitespace-nowrap",
        isCredit ? "text-green-600" : "text-foreground"
      )}>
        {isCredit ? "+" : ""}
        {formatCurrency(Math.abs(amount), txn.currency)}
      </td>
      <td className="px-4 py-2.5">
        <span className="text-xs text-muted-foreground">
          {SOURCE_LABELS[txn.categorization_source] ?? txn.categorization_source}
        </span>
      </td>
    </tr>
  );
}

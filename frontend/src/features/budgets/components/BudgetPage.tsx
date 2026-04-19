/**
 * Budget page — monthly spending summary with a bar chart and category breakdown table.
 */
import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { formatCurrency } from "@/lib/utils";
import { useAvailableMonths, useBudgetSummary } from "../hooks/useBudget";

export function BudgetPage() {
  const { data: months = [] } = useAvailableMonths();
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);

  // Default to most recent month when list loads
  useEffect(() => {
    if (months.length > 0 && !selectedMonth) {
      setSelectedMonth(months[0]);
    }
  }, [months, selectedMonth]);

  const { data: summary, isLoading } = useBudgetSummary(selectedMonth);

  // Only show top N categories in chart for readability
  const chartData = (summary?.by_category ?? [])
    .filter((c) => parseFloat(c.total) > 0)
    .slice(0, 12)
    .map((c) => ({
      name: c.category_name.length > 14 ? c.category_name.slice(0, 13) + "…" : c.category_name,
      fullName: c.category_name,
      amount: parseFloat(c.total),
      color: "#6366f1",
    }));

  function formatMonthLabel(m: string) {
    const [year, month] = m.split("-");
    return new Date(parseInt(year), parseInt(month) - 1).toLocaleDateString("en-US", {
      month: "long",
      year: "numeric",
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-2xl font-bold">Budget Summary</h2>
          <p className="text-muted-foreground text-sm">Monthly spending breakdown</p>
        </div>
        <Select
          value={selectedMonth || ""}
          onChange={(e) => setSelectedMonth(e.target.value || null)}
          className="w-44"
        >
          <option value="">Select month…</option>
          {months.map((m) => (
            <option key={m} value={m}>{formatMonthLabel(m)}</option>
          ))}
        </Select>
      </div>

      {!selectedMonth && (
        <p className="text-muted-foreground text-sm">Select a month to view your budget summary.</p>
      )}

      {isLoading && <p className="text-muted-foreground text-sm">Loading…</p>}

      {summary && (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-3 gap-4">
            <SummaryCard
              label="Total Spend"
              value={formatCurrency(summary.total_spend)}
              className="border-destructive/30"
            />
            <SummaryCard
              label="Total Income / Credits"
              value={formatCurrency(summary.total_income)}
              className="border-green-300"
              valueClassName="text-green-700"
            />
            <SummaryCard
              label="Net"
              value={formatCurrency(summary.net)}
              valueClassName={parseFloat(summary.net) >= 0 ? "text-green-700" : "text-destructive"}
            />
          </div>

          {/* Bar chart */}
          {chartData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Spending by Category</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={chartData} margin={{ top: 0, right: 10, left: 10, bottom: 40 }}>
                    <XAxis
                      dataKey="name"
                      angle={-35}
                      textAnchor="end"
                      tick={{ fontSize: 11 }}
                    />
                    <YAxis
                      tickFormatter={(v) => `$${v.toLocaleString()}`}
                      tick={{ fontSize: 11 }}
                      width={70}
                    />
                    <Tooltip
                      formatter={(value: number, _name, props) => [
                        formatCurrency(value),
                        props.payload.fullName,
                      ]}
                    />
                    <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, i) => (
                        <Cell key={i} fill={`hsl(${245 + i * 12}, 70%, 55%)`} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* Category breakdown table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Category Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-muted-foreground">
                  <tr>
                    <th className="text-left px-4 py-2 font-medium">Category</th>
                    <th className="text-left px-4 py-2 font-medium">Parent</th>
                    <th className="text-right px-4 py-2 font-medium">Transactions</th>
                    <th className="text-right px-4 py-2 font-medium">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {summary.by_category.map((cat, i) => (
                    <tr key={i} className="hover:bg-muted/30">
                      <td className="px-4 py-2.5">{cat.category_name}</td>
                      <td className="px-4 py-2.5 text-muted-foreground text-xs">
                        {cat.parent_category_name || "—"}
                      </td>
                      <td className="px-4 py-2.5 text-right text-muted-foreground">
                        {cat.transaction_count}
                      </td>
                      <td className={`px-4 py-2.5 text-right font-medium ${
                        parseFloat(cat.total) < 0 ? "text-green-700" : ""
                      }`}>
                        {formatCurrency(Math.abs(parseFloat(cat.total)))}
                        {parseFloat(cat.total) < 0 && " ↩"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function SummaryCard({
  label,
  value,
  className,
  valueClassName,
}: {
  label: string;
  value: string;
  className?: string;
  valueClassName?: string;
}) {
  return (
    <Card className={className}>
      <CardContent className="p-5">
        <p className="text-xs text-muted-foreground mb-1">{label}</p>
        <p className={`text-2xl font-bold ${valueClassName || ""}`}>{value}</p>
      </CardContent>
    </Card>
  );
}

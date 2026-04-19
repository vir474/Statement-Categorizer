/**
 * Statements page — upload new statements and view all imported ones.
 * Parse status is polled every 3s while any statement is in "pending" or "parsing" state.
 */
import { useCallback, useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { FileUp, Trash2, RefreshCw, CheckCircle, AlertCircle, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";
import type { Statement } from "@/types";
import { useDeleteStatement, useStatements, useUploadStatement, STATEMENTS_KEY } from "../hooks/useStatements";

function StatusBadge({ status }: { status: Statement["parse_status"] }) {
  if (status === "done") return <Badge variant="success"><CheckCircle size={10} className="mr-1" />Imported</Badge>;
  if (status === "error") return <Badge variant="error"><AlertCircle size={10} className="mr-1" />Error</Badge>;
  if (status === "parsing") return <Badge variant="warning"><RefreshCw size={10} className="mr-1 animate-spin" />Parsing</Badge>;
  return <Badge><Clock size={10} className="mr-1" />Pending</Badge>;
}

export function StatementsPage() {
  const { data: statements = [], isLoading } = useStatements();
  const upload = useUploadStatement();
  const del = useDeleteStatement();
  const qc = useQueryClient();
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll while any statement is still processing
  const hasProcessing = statements.some(
    (s) => s.parse_status === "pending" || s.parse_status === "parsing"
  );

  useEffect(() => {
    if (hasProcessing) {
      pollRef.current = setInterval(() => {
        qc.invalidateQueries({ queryKey: STATEMENTS_KEY });
      }, 3000);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [hasProcessing, qc]);

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      files.forEach((file) => upload.mutate(file));
      e.target.value = "";
    },
    [upload]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      Array.from(e.dataTransfer.files).forEach((file) => upload.mutate(file));
    },
    [upload]
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Statements</h2>
        <p className="text-muted-foreground text-sm mt-1">
          Upload bank or credit card statements (PDF, CSV, OFX, QFX)
        </p>
      </div>

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-border rounded-lg p-10 text-center hover:border-primary transition-colors"
      >
        <FileUp size={36} className="mx-auto text-muted-foreground mb-3" />
        <p className="text-sm text-muted-foreground mb-3">
          Drag & drop files here, or click to browse
        </p>
        <label className="inline-flex items-center justify-center rounded-md border border-input bg-background hover:bg-accent px-3 h-8 text-xs font-medium cursor-pointer transition-colors">
          Choose Files
          <input
            type="file"
            multiple
            accept=".pdf,.csv,.tsv,.ofx,.qfx"
            className="hidden"
            onChange={handleFileChange}
          />
        </label>
        <p className="text-xs text-muted-foreground mt-2">
          Supported: PDF, CSV, OFX, QFX
        </p>
      </div>

      {/* Statement list */}
      {isLoading ? (
        <p className="text-muted-foreground text-sm">Loading…</p>
      ) : statements.length === 0 ? (
        <p className="text-muted-foreground text-sm">No statements imported yet.</p>
      ) : (
        <div className="space-y-3">
          {statements.map((stmt) => (
            <Card key={stmt.id}>
              <CardContent className="p-4 flex items-center justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm truncate">{stmt.account_name || stmt.filename}</span>
                    <StatusBadge status={stmt.parse_status} />
                    <Badge variant="outline" className="text-xs">{stmt.file_format.toUpperCase()}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {stmt.period_start && stmt.period_end
                      ? `${formatDate(stmt.period_start)} – ${formatDate(stmt.period_end)}`
                      : "Date range unknown"}
                    {" · "}
                    {stmt.transaction_count} transactions
                    {" · "}
                    Uploaded {formatDate(stmt.uploaded_at.split("T")[0])}
                  </p>
                  {stmt.parse_error && (
                    <p className="text-xs text-destructive mt-1">{stmt.parse_error}</p>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => del.mutate(stmt.id)}
                  className="text-muted-foreground hover:text-destructive shrink-0"
                >
                  <Trash2 size={14} />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

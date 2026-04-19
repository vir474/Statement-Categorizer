/**
 * Root app component — handles client-side routing via hash-based navigation.
 * Using simple hash routing to avoid needing a server for history API (works offline + on file://).
 */
import { useState, useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sidebar } from "@/components/layout/Sidebar";
import { StatementsPage } from "@/features/statements/components/StatementsPage";
import { TransactionsPage } from "@/features/transactions/components/TransactionsPage";
import { CategoriesPage } from "@/features/categories/components/CategoriesPage";
import { BudgetPage } from "@/features/budgets/components/BudgetPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Keep data fresh for 30 seconds before refetching
      staleTime: 30_000,
      retry: 1,
    },
  },
});

function getPath(): string {
  return window.location.hash.replace("#", "") || "/";
}

export function App() {
  const [currentPath, setCurrentPath] = useState(getPath);

  useEffect(() => {
    const handler = () => setCurrentPath(getPath());
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  function navigate(href: string) {
    window.location.hash = href;
  }

  function renderPage() {
    if (currentPath === "/") return <StatementsPage />;
    if (currentPath === "/transactions") return <TransactionsPage />;
    if (currentPath === "/categories") return <CategoriesPage />;
    if (currentPath === "/budget") return <BudgetPage />;
    return <StatementsPage />;
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex h-screen overflow-hidden bg-background">
        <Sidebar currentPath={currentPath} onNavigate={navigate} />
        <main className="flex-1 overflow-auto p-6">
          {renderPage()}
        </main>
      </div>
    </QueryClientProvider>
  );
}

import { cn } from "@/lib/utils";
import { BarChart3, CreditCard, FileUp, Tags } from "lucide-react";

const navItems = [
  { label: "Statements", icon: FileUp, href: "/" },
  { label: "Transactions", icon: CreditCard, href: "/transactions" },
  { label: "Categories", icon: Tags, href: "/categories" },
  { label: "Budget", icon: BarChart3, href: "/budget" },
];

interface SidebarProps {
  currentPath: string;
  onNavigate: (href: string) => void;
}

export function Sidebar({ currentPath, onNavigate }: SidebarProps) {
  return (
    <aside className="w-56 shrink-0 border-r bg-muted/30 flex flex-col">
      <div className="p-5 border-b">
        <h1 className="font-bold text-base tracking-tight">Statement Categorizer</h1>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map(({ label, icon: Icon, href }) => (
          <button
            key={href}
            onClick={() => onNavigate(href)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
              currentPath === href
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            )}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </nav>
    </aside>
  );
}

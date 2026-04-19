import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merges Tailwind classes safely, resolving conflicts. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format a decimal amount as currency string. */
export function formatCurrency(amount: number | string, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency }).format(Number(amount));
}

/** Format ISO date string as "Jan 15, 2024". */
export function formatDate(dateStr: string): string {
  return new Date(dateStr + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

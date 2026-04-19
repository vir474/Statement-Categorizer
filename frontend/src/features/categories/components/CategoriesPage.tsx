/**
 * Categories page — manage categories and their auto-categorization rules.
 * Hierarchical display: parent categories expand to show sub-categories + rules.
 */
import { useState } from "react";
import { ChevronDown, ChevronRight, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { Category } from "@/types";
import {
  useCategories, useCreateCategory, useDeleteCategory,
  useRules, useCreateRule, useDeleteRule,
} from "../hooks/useCategories";

export function CategoriesPage() {
  const { data: categories = [], isLoading } = useCategories();
  const createCat = useCreateCategory();
  const [newName, setNewName] = useState("");
  const [newColor, setNewColor] = useState("#6366f1");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const topLevel = categories.filter((c) => !c.parent_id);
  const subFor = (parentId: number) => categories.filter((c) => c.parent_id === parentId);

  function handleCreate(e: React.FormEvent, parentId?: number) {
    e.preventDefault();
    if (!newName.trim()) return;
    createCat.mutate({ name: newName.trim(), color: newColor, parent_id: parentId ?? null });
    setNewName("");
  }

  if (isLoading) return <p className="text-muted-foreground text-sm">Loading…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Categories</h2>
        <p className="text-muted-foreground text-sm mt-1">
          Manage categories and rules for auto-categorization
        </p>
      </div>

      {/* Add top-level category */}
      <form onSubmit={(e) => handleCreate(e)} className="flex gap-2">
        <Input
          placeholder="New category name…"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          className="max-w-xs"
        />
        <input type="color" value={newColor} onChange={(e) => setNewColor(e.target.value)}
          className="h-9 w-9 rounded border cursor-pointer" title="Pick color" />
        <Button type="submit" size="sm" disabled={!newName.trim()}>
          <Plus size={14} className="mr-1" /> Add Category
        </Button>
      </form>

      {/* Category list */}
      <div className="space-y-2">
        {topLevel.map((cat) => (
          <CategoryRow
            key={cat.id}
            category={cat}
            subCategories={subFor(cat.id)}
            expanded={expandedId === cat.id}
            onToggle={() => setExpandedId(expandedId === cat.id ? null : cat.id)}
            allCategories={categories}
          />
        ))}
      </div>
    </div>
  );
}

function CategoryRow({
  category,
  subCategories,
  expanded,
  onToggle,
  allCategories,
}: {
  category: Category;
  subCategories: Category[];
  expanded: boolean;
  onToggle: () => void;
  allCategories: Category[];
}) {
  const del = useDeleteCategory();
  const createCat = useCreateCategory();
  const [newSubName, setNewSubName] = useState("");
  const [showAddSub, setShowAddSub] = useState(false);

  return (
    <Card>
      <CardContent className="p-0">
        {/* Parent row */}
        <div className="flex items-center gap-3 px-4 py-3">
          <button onClick={onToggle} className="text-muted-foreground hover:text-foreground">
            {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
          <span
            className="w-3 h-3 rounded-full shrink-0"
            style={{ backgroundColor: category.color }}
          />
          <span className="font-medium text-sm flex-1">{category.name}</span>
          {!category.is_user_defined && (
            <Badge variant="outline" className="text-xs">Default</Badge>
          )}
          <span className="text-xs text-muted-foreground">{subCategories.length} sub</span>
          <Button
            variant="ghost" size="sm"
            onClick={() => setShowAddSub(!showAddSub)}
            className="text-muted-foreground"
          >
            <Plus size={14} />
          </Button>
          <Button
            variant="ghost" size="sm"
            onClick={() => del.mutate(category.id)}
            className="text-muted-foreground hover:text-destructive"
          >
            <Trash2 size={14} />
          </Button>
        </div>

        {/* Add sub-category form */}
        {showAddSub && (
          <div className="px-10 pb-3 flex gap-2">
            <Input
              placeholder="Sub-category name…"
              value={newSubName}
              onChange={(e) => setNewSubName(e.target.value)}
              className="max-w-xs h-7 text-xs"
            />
            <Button
              size="sm"
              onClick={() => {
                if (newSubName.trim()) {
                  createCat.mutate({ name: newSubName.trim(), parent_id: category.id });
                  setNewSubName("");
                  setShowAddSub(false);
                }
              }}
              className="h-7 text-xs"
            >
              Add
            </Button>
          </div>
        )}

        {/* Sub-categories expanded */}
        {expanded && (
          <div className="border-t divide-y">
            {subCategories.length === 0 ? (
              <p className="px-10 py-3 text-xs text-muted-foreground">No sub-categories yet.</p>
            ) : (
              subCategories.map((sub) => (
                <SubCategoryRow key={sub.id} category={sub} />
              ))
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SubCategoryRow({ category }: { category: Category }) {
  const del = useDeleteCategory();
  const delRule = useDeleteRule(category.id);
  const createRule = useCreateRule(category.id);
  const { data: rules = [] } = useRules(category.id);
  const [newPattern, setNewPattern] = useState("");
  const [isRegex, setIsRegex] = useState(false);

  return (
    <div className="px-10 py-3 space-y-2">
      <div className="flex items-center gap-3">
        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: category.color }} />
        <span className="text-sm font-medium flex-1">{category.name}</span>
        <Button
          variant="ghost" size="sm"
          onClick={() => del.mutate(category.id)}
          className="text-muted-foreground hover:text-destructive h-6 w-6 p-0"
        >
          <Trash2 size={12} />
        </Button>
      </div>

      {/* Rules */}
      <div className="space-y-1 pl-5">
        {rules.map((rule) => (
          <div key={rule.id} className="flex items-center gap-2 text-xs">
            <code className="bg-muted px-1.5 py-0.5 rounded">{rule.pattern}</code>
            {rule.is_regex && <Badge variant="outline" className="text-xs py-0">regex</Badge>}
            <button
              onClick={() => delRule.mutate(rule.id)}
              className="text-muted-foreground hover:text-destructive"
            >
              <Trash2 size={11} />
            </button>
          </div>
        ))}

        {/* Add rule */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (newPattern.trim()) {
              createRule.mutate({ pattern: newPattern.trim(), is_regex: isRegex, priority: 100 });
              setNewPattern("");
            }
          }}
          className="flex gap-1.5 mt-1"
        >
          <Input
            placeholder="Add rule pattern…"
            value={newPattern}
            onChange={(e) => setNewPattern(e.target.value)}
            className="h-6 text-xs max-w-48"
          />
          <label className="flex items-center gap-1 text-xs cursor-pointer">
            <input type="checkbox" checked={isRegex} onChange={(e) => setIsRegex(e.target.checked)} />
            regex
          </label>
          <Button type="submit" size="sm" className="h-6 text-xs px-2">Add</Button>
        </form>
      </div>
    </div>
  );
}

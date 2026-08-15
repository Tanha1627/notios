import React, { useMemo, useState } from "react";

function buildTree(pages) {
  const byParent = {};
  pages.forEach((p) => {
    const key = p.parentPageId || "root";
    if (!byParent[key]) byParent[key] = [];
    byParent[key].push(p);
  });
  return byParent;
}

export default function PageTree({
  pages,
  selectedPageId,
  onSelect,
  onCreateChild,
  canEditPage,
}) {
  const byParent = useMemo(() => buildTree(pages), [pages]);

  if (!pages.length) {
    return (
      <p className="text-xs text-subink px-3 py-4 leading-relaxed">
        No pages yet. Use "New page" above to create the first one.
      </p>
    );
  }

  return (
    <div className="space-y-0.5">
      {(byParent["root"] || []).map((page) => (
        <TreeNode
          key={page.id}
          page={page}
          depth={0}
          byParent={byParent}
          selectedPageId={selectedPageId}
          onSelect={onSelect}
          onCreateChild={onCreateChild}
          canEditPage={canEditPage}
        />
      ))}
    </div>
  );
}

function TreeNode({ page, depth, byParent, selectedPageId, onSelect, onCreateChild, canEditPage }) {
  const [expanded, setExpanded] = useState(true);
  const children = byParent[page.id] || [];
  const hasChildren = children.length > 0;
  const isSelected = page.id === selectedPageId;

  return (
    <div>
      <div
        className={`group flex items-center gap-1 rounded-md pr-1.5 cursor-pointer text-sm ${
          isSelected ? "bg-pine-100/70" : "hover:bg-pine-50"
        }`}
        style={{ paddingLeft: `${8 + depth * 16}px` }}
      >
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          className={`w-4 h-4 flex items-center justify-center text-subink/60 shrink-0 ${
            hasChildren ? "" : "invisible"
          }`}
          tabIndex={hasChildren ? 0 : -1}
        >
          {expanded ? "▾" : "▸"}
        </button>
        <button
          type="button"
          onClick={() => onSelect(page.id)}
          className={`flex-1 text-left truncate py-1.5 ${
            isSelected ? "text-pine-700 font-medium" : "text-ink"
          }`}
          title={page.title}
        >
          {page.title}
        </button>
        {canEditPage(page) && (
          <button
            type="button"
            onClick={() => onCreateChild(page.id)}
            className="opacity-0 group-hover:opacity-100 text-subink hover:text-pine-600 w-5 h-5 flex items-center justify-center text-xs transition-opacity"
            title="New sub-page"
          >
            +
          </button>
        )}
      </div>
      {expanded && hasChildren && (
        <div>
          {children.map((child) => (
            <TreeNode
              key={child.id}
              page={child}
              depth={depth + 1}
              byParent={byParent}
              selectedPageId={selectedPageId}
              onSelect={onSelect}
              onCreateChild={onCreateChild}
              canEditPage={canEditPage}
            />
          ))}
        </div>
      )}
    </div>
  );
}

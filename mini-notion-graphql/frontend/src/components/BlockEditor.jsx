import React, { useState } from "react";

const TYPE_META = {
  heading: { label: "H", class: "text-xl font-display font-medium" },
  text: { label: "T", class: "text-sm" },
  bullet: { label: "•", class: "text-sm" },
  todo: { label: "☐", class: "text-sm" },
};

export default function BlockEditor({ blocks, canEdit, onUpdate, onDelete, onCreate }) {
  return (
    <div className="space-y-1">
      {blocks
        .slice()
        .sort((a, b) => a.position - b.position)
        .map((block) => (
          <BlockRow
            key={block.id}
            block={block}
            canEdit={canEdit}
            onUpdate={onUpdate}
            onDelete={onDelete}
          />
        ))}

      {canEdit && <AddBlockRow onCreate={onCreate} nextPosition={blocks.length} />}

      {!canEdit && blocks.length === 0 && (
        <p className="text-sm text-subink italic">This page has no content yet.</p>
      )}
    </div>
  );
}

function BlockRow({ block, canEdit, onUpdate, onDelete }) {
  const [text, setText] = useState(block.content?.text || "");
  const [checked, setChecked] = useState(Boolean(block.content?.checked));
  const meta = TYPE_META[block.type] || TYPE_META.text;

  function commit(nextText = text, nextChecked = checked) {
    onUpdate(block.id, { text: nextText, checked: nextChecked });
  }

  return (
    <div className="group flex items-start gap-2 rounded-md px-2 py-1 hover:bg-pine-50/60">
      <span className="w-5 pt-1 text-center text-xs font-mono text-subink/50 select-none">
        {block.type === "todo" ? (
          <input
            type="checkbox"
            checked={checked}
            disabled={!canEdit}
            onChange={(e) => {
              setChecked(e.target.checked);
              commit(text, e.target.checked);
            }}
          />
        ) : (
          meta.label
        )}
      </span>
      <textarea
        className={`flex-1 bg-transparent resize-none focus:outline-none py-1 ${meta.class} ${
          block.type === "todo" && checked ? "line-through text-subink" : "text-ink"
        }`}
        rows={1}
        value={text}
        disabled={!canEdit}
        onChange={(e) => {
          setText(e.target.value);
          e.target.style.height = "auto";
          e.target.style.height = e.target.scrollHeight + "px";
        }}
        onBlur={() => commit()}
        placeholder={canEdit ? "Type something…" : ""}
      />
      {canEdit && (
        <button
          type="button"
          onClick={() => onDelete(block.id)}
          className="opacity-0 group-hover:opacity-100 text-subink hover:text-red-600 text-xs px-1 py-1 transition-opacity"
          title="Delete block"
        >
          ✕
        </button>
      )}
    </div>
  );
}

function AddBlockRow({ onCreate, nextPosition }) {
  const [open, setOpen] = useState(false);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="text-sm text-subink hover:text-pine-600 px-2 py-1.5 rounded-md hover:bg-pine-50/60 transition-colors"
      >
        + Add block
      </button>
    );
  }

  return (
    <div className="flex items-center gap-2 px-2 py-1">
      {Object.entries(TYPE_META).map(([type, meta]) => (
        <button
          key={type}
          type="button"
          onClick={() => {
            onCreate(type, nextPosition);
            setOpen(false);
          }}
          className="font-mono text-xs px-2.5 py-1 rounded-full border border-line bg-surface hover:border-pine-300 hover:text-pine-700 text-subink transition-colors"
        >
          {meta.label} {type}
        </button>
      ))}
      <button
        type="button"
        onClick={() => setOpen(false)}
        className="text-xs text-subink hover:text-ink px-1"
      >
        cancel
      </button>
    </div>
  );
}

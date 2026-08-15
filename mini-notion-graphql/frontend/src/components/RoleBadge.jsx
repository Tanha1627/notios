import React from "react";

const STYLES = {
  owner: "bg-amber-100 text-amber-700",
  editor: "bg-pine-100 text-pine-700",
  viewer: "bg-slate-100 text-slate-500",
};

export default function RoleBadge({ role, size = "sm" }) {
  if (!role) return null;
  const px = size === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs";
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-mono uppercase tracking-wide ${STYLES[role] || "bg-slate-100 text-slate-500"} ${px}`}
    >
      {role}
    </span>
  );
}

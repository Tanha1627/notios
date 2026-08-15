import React, { useEffect, useState } from "react";
import { api } from "../api/graphql";
import { useAuth } from "../context/AuthContext.jsx";
import RoleBadge from "./RoleBadge.jsx";

export default function ShareModal({ page, onClose }) {
  const { token } = useAuth();
  const [permissions, setPermissions] = useState([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("editor");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    const data = await api.pagePermissions(token, page.id);
    setPermissions(data.pagePermissions);
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page.id]);

  async function handleShare(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const found = await api.userByEmail(token, email);
      if (!found.userByEmail) {
        setError("No user found with that email. They need to register first.");
        return;
      }
      await api.sharePage(token, { pageId: page.id, userId: found.userByEmail.id, role });
      setEmail("");
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleRevoke(userId) {
    await api.revokeAccess(token, { pageId: page.id, userId });
    await refresh();
  }

  return (
    <div className="fixed inset-0 bg-ink/30 backdrop-blur-[2px] flex items-center justify-center z-50 p-4">
      <div className="bg-surface rounded-card shadow-panel w-full max-w-md p-6">
        <div className="flex items-start justify-between mb-1">
          <h3 className="font-display text-lg text-ink">Share “{page.title}”</h3>
          <button onClick={onClose} className="text-subink hover:text-ink text-sm">
            ✕
          </button>
        </div>
        <p className="text-xs text-subink mb-4">
          Sub-pages inherit this access unless they're shared separately.
        </p>

        <form onSubmit={handleShare} className="flex gap-2 mb-4">
          <input
            type="email"
            required
            placeholder="person@example.com"
            className="input flex-1"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <select
            className="input w-28"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option value="viewer">viewer</option>
            <option value="editor">editor</option>
            <option value="owner">owner</option>
          </select>
          <button
            type="submit"
            disabled={busy}
            className="bg-pine-500 hover:bg-pine-600 disabled:opacity-60 text-paper text-sm font-medium rounded-card px-3 shrink-0"
          >
            Share
          </button>
        </form>

        {error && (
          <p className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-card px-3 py-2 mb-4">
            {error}
          </p>
        )}

        <div className="space-y-1">
          <p className="text-xs font-mono uppercase tracking-wide text-subink mb-2">
            People with access
          </p>
          {permissions.length === 0 && (
            <p className="text-sm text-subink">No one has been given explicit access yet.</p>
          )}
          {permissions.map((p) => (
            <div
              key={p.id}
              className="flex items-center justify-between py-1.5 border-b border-line last:border-0"
            >
              <span className="text-sm font-mono text-ink truncate">{p.userId}</span>
              <div className="flex items-center gap-2 shrink-0">
                <RoleBadge role={p.role} />
                <button
                  onClick={() => handleRevoke(p.userId)}
                  className="text-xs text-subink hover:text-red-600"
                >
                  Revoke
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

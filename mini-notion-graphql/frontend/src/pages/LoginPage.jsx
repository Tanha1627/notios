import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const DEMO_ACCOUNTS = [
  { label: "owner", email: "owner@example.com" },
  { label: "editor", email: "editor@example.com" },
  { label: "viewer", email: "viewer@example.com" },
];

export default function LoginPage() {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, name, password);
      }
      navigate("/");
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen w-full flex bg-paper">
      {/* Left: illustrative signature panel */}
      <div className="hidden lg:flex lg:w-[46%] bg-pine-700 text-paper flex-col justify-between p-12 relative overflow-hidden">
        <div className="relative z-10">
          <div className="font-mono text-xs uppercase tracking-[0.2em] text-pine-100/70">
            notio
          </div>
          <h1 className="font-display text-4xl mt-3 leading-tight">
            Pages nest.
            <br />
            Access follows.
          </h1>
          <p className="text-pine-100/80 mt-4 max-w-sm text-[15px] leading-relaxed">
            Share a page and everything underneath it inherits that access —
            until a page says otherwise.
          </p>
        </div>

        <PageTreeIllustration />

        <div className="relative z-10 font-mono text-xs text-pine-100/50">
          FastAPI &middot; GraphQL &middot; Postgres
        </div>
      </div>

      {/* Right: auth form */}
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <div className="lg:hidden font-mono text-xs uppercase tracking-[0.2em] text-subink mb-2">
            notio
          </div>
          <h2 className="font-display text-2xl text-ink">
            {mode === "login" ? "Welcome back" : "Create your account"}
          </h2>
          <p className="text-subink text-sm mt-1 mb-6">
            {mode === "login"
              ? "Sign in to open your workspace."
              : "Takes about ten seconds."}
          </p>

          <form onSubmit={handleSubmit} className="space-y-3">
            {mode === "register" && (
              <Field label="Name">
                <input
                  className="input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="Ada Lovelace"
                />
              </Field>
            )}
            <Field label="Email">
              <input
                type="email"
                className="input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                autoComplete="username"
              />
            </Field>
            <Field label="Password">
              <input
                type="password"
                className="input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
              />
            </Field>

            {error && (
              <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-card px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full bg-pine-500 hover:bg-pine-600 disabled:opacity-60 text-paper font-medium text-sm rounded-card py-2.5 transition-colors"
            >
              {busy ? "Working…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <button
            className="mt-4 text-sm text-subink hover:text-ink transition-colors"
            onClick={() => {
              setError("");
              setMode(mode === "login" ? "register" : "login");
            }}
          >
            {mode === "login"
              ? "New here? Create an account →"
              : "← Already have an account? Sign in"}
          </button>

          {mode === "login" && (
            <div className="mt-8 pt-6 border-t border-line">
              <p className="text-xs text-subink mb-2 font-mono uppercase tracking-wide">
                Seeded demo accounts
              </p>
              <div className="flex flex-wrap gap-2">
                {DEMO_ACCOUNTS.map((acc) => (
                  <button
                    key={acc.email}
                    type="button"
                    onClick={() => {
                      setEmail(acc.email);
                      setPassword("password123");
                    }}
                    className="font-mono text-xs px-2.5 py-1 rounded-full border border-line bg-surface hover:border-pine-300 text-subink hover:text-pine-700 transition-colors"
                  >
                    {acc.label}
                  </button>
                ))}
              </div>
              <p className="text-xs text-subink mt-2">
                Run <code className="font-mono">python -m app.seed</code> in the backend first.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="block text-xs font-medium text-subink mb-1">{label}</span>
      {children}
    </label>
  );
}

function PageTreeIllustration() {
  const rows = [
    { depth: 0, label: "Product Roadmap", role: "owner" },
    { depth: 1, label: "Q3 Launch Plan", role: "owner" },
    { depth: 1, label: "Engineering Notes", role: "editor" },
    { depth: 2, label: "API Design Decisions", role: "editor" },
  ];
  const roleColor = { owner: "bg-amber-500", editor: "bg-pine-300", viewer: "bg-slate-500" };

  return (
    <div className="relative z-10 bg-pine-600/40 border border-pine-100/10 rounded-card p-5 backdrop-blur-sm">
      <div className="space-y-2.5">
        {rows.map((r, i) => (
          <div
            key={i}
            className="flex items-center gap-2 text-sm font-mono"
            style={{ paddingLeft: `${r.depth * 18}px` }}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${roleColor[r.role]}`} />
            <span className="text-pine-50/90">{r.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

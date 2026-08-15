import React, { useEffect, useState, useCallback } from "react";
import { api, GraphQLError } from "../api/graphql";
import { useAuth } from "../context/AuthContext.jsx";
import PageTree from "../components/PageTree.jsx";
import BlockEditor from "../components/BlockEditor.jsx";
import RoleBadge from "../components/RoleBadge.jsx";
import ShareModal from "../components/ShareModal.jsx";

export default function WorkspacePage() {
  const { token, user, logout } = useAuth();

  const [workspaces, setWorkspaces] = useState([]);
  const [workspaceId, setWorkspaceId] = useState(null);

  const [pages, setPages] = useState([]);
  const [selectedPageId, setSelectedPageId] = useState(null);
  const [blocks, setBlocks] = useState([]);

  const [search, setSearch] = useState("");
  const [loadingWs, setLoadingWs] = useState(true);
  const [shareOpen, setShareOpen] = useState(false);
  const [banner, setBanner] = useState("");

  const selectedPage = pages.find((p) => p.id === selectedPageId) || null;
  const canEdit = selectedPage && ["owner", "editor"].includes(selectedPage.myRole);
  const canManage = selectedPage && selectedPage.myRole === "owner";

  // --- bootstrap: load workspaces, auto-create one if the user has none ---
  useEffect(() => {
    (async () => {
      const data = await api.myWorkspaces(token);
      let ws = data.myWorkspaces;
      if (ws.length === 0) {
        const created = await api.createWorkspace(token, `${user?.name || "My"}'s Workspace`);
        ws = [created.createWorkspace];
      }
      setWorkspaces(ws);
      setWorkspaceId(ws[0].id);
      setLoadingWs(false);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const loadPages = useCallback(
    async (wsId, searchTerm) => {
      if (!wsId) return;
      const data = await api.pages(token, wsId, searchTerm || null);
      setPages(data.pages);
    },
    [token]
  );

  useEffect(() => {
    if (workspaceId) loadPages(workspaceId, search);
  }, [workspaceId, loadPages]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!selectedPageId) {
      setBlocks([]);
      return;
    }
    api.blocks(token, selectedPageId).then((data) => setBlocks(data.blocks));
  }, [selectedPageId, token]);

  async function handleSearch(e) {
    e.preventDefault();
    await loadPages(workspaceId, search);
  }

  async function handleCreatePage(parentPageId = null) {
    const title = parentPageId ? "Untitled sub-page" : "Untitled page";
    const data = await api.createPage(token, { workspaceId, title, parentPageId });
    await loadPages(workspaceId, search);
    setSelectedPageId(data.createPage.id);
  }

  async function handleRenamePage(title) {
    if (!selectedPage) return;
    await api.updatePageTitle(token, selectedPage.id, title);
    await loadPages(workspaceId, search);
  }

  async function handleDeletePage() {
    if (!selectedPage) return;
    if (!confirm(`Delete "${selectedPage.title}" and everything nested under it?`)) return;
    await api.deletePage(token, selectedPage.id);
    setSelectedPageId(null);
    await loadPages(workspaceId, search);
  }

  async function handleCreateBlock(type, position) {
    const data = await api.createBlock(token, {
      pageId: selectedPageId,
      type,
      content: { text: "" },
      position,
    });
    setBlocks((b) => [...b, data.createBlock]);
  }

  async function handleUpdateBlock(blockId, content) {
    try {
      await api.updateBlock(token, { blockId, content });
      setBlocks((bs) => bs.map((b) => (b.id === blockId ? { ...b, content } : b)));
    } catch (err) {
      flashError(err);
    }
  }

  async function handleDeleteBlock(blockId) {
    await api.deleteBlock(token, blockId);
    setBlocks((bs) => bs.filter((b) => b.id !== blockId));
  }

  function flashError(err) {
    setBanner(err instanceof GraphQLError ? err.message : "Something went wrong.");
    setTimeout(() => setBanner(""), 4000);
  }

  if (loadingWs) {
    return (
      <div className="h-screen flex items-center justify-center text-subink font-mono text-sm">
        setting up your workspace…
      </div>
    );
  }

  return (
    <div className="h-screen w-full flex bg-paper">
      {/* Sidebar */}
      <aside className="w-72 shrink-0 border-r border-line flex flex-col bg-surface/60">
        <div className="p-4 border-b border-line">
          <div className="flex items-center justify-between mb-3">
            <span className="font-mono text-xs uppercase tracking-[0.2em] text-subink">
              notio
            </span>
            <button
              onClick={logout}
              className="text-xs text-subink hover:text-ink"
              title="Sign out"
            >
              sign out
            </button>
          </div>
          <div className="text-sm text-ink font-medium truncate">{user?.name}</div>
          <div className="text-xs text-subink font-mono truncate">{user?.email}</div>
        </div>

        <div className="p-3 border-b border-line">
          <form onSubmit={handleSearch}>
            <input
              className="input text-xs"
              placeholder="Search this workspace…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </form>
        </div>

        <div className="flex items-center justify-between px-3 pt-3 pb-1">
          <span className="text-xs font-mono uppercase tracking-wide text-subink">Pages</span>
          <button
            onClick={() => handleCreatePage(null)}
            className="text-xs text-pine-600 hover:text-pine-700 font-medium"
          >
            + New page
          </button>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin px-2 pb-4">
          <PageTree
            pages={pages}
            selectedPageId={selectedPageId}
            onSelect={setSelectedPageId}
            onCreateChild={handleCreatePage}
            canEditPage={(p) => ["owner", "editor"].includes(p.myRole)}
          />
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {banner && (
          <div className="bg-red-50 border-b border-red-200 text-red-700 text-sm px-6 py-2">
            {banner}
          </div>
        )}

        {!selectedPage ? (
          <EmptyState onCreate={() => handleCreatePage(null)} />
        ) : (
          <div className="flex-1 overflow-y-auto scrollbar-thin">
            <div className="max-w-2xl mx-auto px-10 py-12">
              <div className="flex items-center gap-2 mb-4">
                <RoleBadge role={selectedPage.myRole} size="md" />
                {canManage && (
                  <>
                    <button
                      onClick={() => setShareOpen(true)}
                      className="text-xs text-subink hover:text-pine-700 border border-line rounded-full px-2.5 py-1 hover:border-pine-300 transition-colors"
                    >
                      Share
                    </button>
                    <button
                      onClick={handleDeletePage}
                      className="text-xs text-subink hover:text-red-600 border border-line rounded-full px-2.5 py-1 hover:border-red-200 transition-colors"
                    >
                      Delete page
                    </button>
                  </>
                )}
              </div>

              <TitleEditor
                key={selectedPage.id}
                title={selectedPage.title}
                editable={canEdit}
                onCommit={handleRenamePage}
              />

              <div className="mt-8">
                <BlockEditor
                  blocks={blocks}
                  canEdit={canEdit}
                  onCreate={handleCreateBlock}
                  onUpdate={handleUpdateBlock}
                  onDelete={handleDeleteBlock}
                />
              </div>
            </div>
          </div>
        )}
      </main>

      {shareOpen && selectedPage && (
        <ShareModal page={selectedPage} onClose={() => setShareOpen(false)} />
      )}
    </div>
  );
}

function TitleEditor({ title, editable, onCommit }) {
  const [value, setValue] = useState(title);
  return (
    <input
      className="w-full font-display text-3xl bg-transparent focus:outline-none text-ink placeholder:text-subink/50"
      value={value}
      disabled={!editable}
      onChange={(e) => setValue(e.target.value)}
      onBlur={() => value.trim() && value !== title && onCommit(value.trim())}
      placeholder="Untitled"
    />
  );
}

function EmptyState({ onCreate }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
      <p className="font-display text-2xl text-ink mb-2">Nothing selected yet</p>
      <p className="text-sm text-subink max-w-xs mb-5">
        Pick a page from the sidebar, or start a new one from scratch.
      </p>
      <button
        onClick={onCreate}
        className="bg-pine-500 hover:bg-pine-600 text-paper text-sm font-medium rounded-card px-4 py-2 transition-colors"
      >
        + New page
      </button>
    </div>
  );
}

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const API =
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000";

const apiFetch = (url, options = {}) =>
  window.fetch(url, {
    ...options,
    credentials: "include",
  });

function Login({ onSuccess }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      const response = await apiFetch(`${API}/api/admin/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ password }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      onSuccess();
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="admin-login-shell">
      <form className="admin-login-card" onSubmit={submit}>
        <div className="brand-orb">✦</div>
        <div className="eyebrow">JAIN AI · SECURE ADMIN</div>
        <h1>Knowledge Console</h1>
        <p>Sign in to approve sources, publish content and manage the knowledge graph.</p>

        <input
          type="password"
          placeholder="Admin password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoFocus
          required
        />

        {error && <div className="login-error">{error}</div>}

        <button className="approve" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}

const host = (url) => {
  try { return new URL(url).hostname.replace("www.", ""); }
  catch { return url || "Unknown source"; }
};

function App() {
  const [sources, setSources] = useState([]);
  const [stats, setStats] = useState({});
  const [missing, setMissing] = useState([]);
  const [graph, setGraph] = useState([]);
  const [filter, setFilter] = useState("pending_review");
  const [busy, setBusy] = useState({});
  const [preview, setPreview] = useState(null);
  const [notice, setNotice] = useState("");
  const [authenticated, setAuthenticated] = useState(null);
  const [cmsOpen,setCmsOpen]=useState(false); const [contentItems,setContentItems]=useState([]);

  useEffect(() => {
    apiFetch(`${API}/api/admin/me`)
      .then((response) => setAuthenticated(response.ok))
      .catch(() => setAuthenticated(false));
  }, []);

  const load = useCallback(async () => {
    const [sourceRes, statRes, graphRes] = await Promise.all([
      apiFetch(`${API}/api/sources?status=${filter}&limit=200`),
      apiFetch(`${API}/api/admin/stats`),
      apiFetch(`${API}/api/admin/graph?limit=12`),
    ]);

    if (!sourceRes.ok || !statRes.ok || !graphRes.ok) {
      throw new Error("Could not load admin data. Is the backend running?");
    }

    const sourceJson = await sourceRes.json();
    const statJson = await statRes.json();
    const graphJson = await graphRes.json();

    setSources(sourceJson.items || []);
    setStats(statJson.stats || {});
    setMissing(statJson.missing_knowledge || []);
    setGraph(graphJson.relationships || []);
    apiFetch(`${API}/api/admin/content`).then(r=>r.json()).then(d=>setContentItems(d.items||[])).catch(()=>{});
  }, [filter]);

  useEffect(() => {
    if (authenticated) {
      load().catch((e) => setNotice(e.message));
    }
  }, [load, authenticated]);

  if (authenticated === null) {
    return (
      <div className="admin-login-shell">
        <div className="admin-login-card">
          <div className="brand-orb">✦</div>
          <h2>Checking secure session…</h2>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return <Login onSuccess={() => setAuthenticated(true)} />;
  }

  const act = async (source, action) => {
    setBusy((x) => ({ ...x, [source.id]: action }));
    setNotice("");

    try {
      const res = await apiFetch(`${API}/api/sources/${source.id}/${action}`, {
        method: "POST",
      });
      const data = await res.json();

      if (!res.ok) throw new Error(data.detail || "Action failed");

      if (action === "approve") {
        setNotice(
          `✓ Approved & indexed: ${source.title || host(source.url)} · ` +
          `${data.ingestion?.chunks || 0} chunks · ` +
          `${data.graph?.entities || 0} graph entities`
        );
      } else {
        setNotice(`Source rejected: ${source.title || host(source.url)}`);
      }

      await load();
    } catch (e) {
      setNotice(e.message);
    } finally {
      setBusy((x) => ({ ...x, [source.id]: null }));
    }
  };

  const filteredLabel = useMemo(() => ({
    pending_review: "Review Queue",
    approved: "Approved Knowledge",
    rejected: "Rejected Sources",
  }[filter] || "Sources"), [filter]);

  return (
    <div className="admin-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-orb">✦</div>
          <div>
            <strong>Jain AI</strong>
            <span>Knowledge Console</span>
          </div>
        </div>

        <nav>
          <button className={filter === "pending_review" ? "active" : ""} onClick={() => setFilter("pending_review")}>
            <span>◎</span> Source Approval <b>{stats.pending || 0}</b>
          </button>
          <button className={filter === "approved" ? "active" : ""} onClick={() => setFilter("approved")}>
            <span>✓</span> Knowledge Base <b>{stats.approved || 0}</b>
          </button>
          <button className={filter === "rejected" ? "active" : ""} onClick={() => setFilter("rejected")}>
            <span>×</span> Rejected <b>{stats.rejected || 0}</b>
          </button>
          <button className={cmsOpen ? "active" : ""} onClick={() => setCmsOpen(!cmsOpen)}><span>▤</span> Content CMS <b>{contentItems.length}</b></button>
        </nav>

        <div className="sidebar-note">
          <span className="pulse" />
          Ollama + pgvector online
          <small>Live discoveries require your approval.</small>
        </div>
      </aside>

      <main>
        <header>
          <div>
            <div className="eyebrow">JAIN AI · ADMIN</div>
            <h1>{filteredLabel}</h1>
            <p>Curate the knowledge Jain AI can trust. One click crawls, embeds and builds graph connections.</p>
          </div>
          <div className="header-actions">
            <button className="refresh" onClick={() => load()}>↻ Refresh</button>
            <button
              className="refresh"
              onClick={async () => {
                await apiFetch(`${API}/api/admin/logout`, { method: "POST" });
                setAuthenticated(false);
              }}
            >
              Sign out
            </button>
          </div>
        </header>

        <section className="metrics">
          <Metric label="Pending review" value={stats.pending || 0} note="Needs your decision" />
          <Metric label="Approved" value={stats.approved || 0} note="Searchable in pgvector" />
          <Metric label="Discovered today" value={stats.discovered_today || 0} note="Found by live search" />
          <Metric label="Total sources" value={stats.total || 0} note="Knowledge registry" />
        </section>

        {notice && <div className="notice">{notice}</div>}

        {filter === "pending_review" && missing.length > 0 && (
          <section className="demand">
            <div className="section-title">
              <div>
                <span className="eyebrow">USER DEMAND</span>
                <h2>Most requested missing knowledge</h2>
              </div>
            </div>
            <div className="demand-row">
              {missing.slice(0, 6).map((item, i) => (
                <div className="demand-chip" key={`${item.discovered_query}-${i}`}>
                  <strong>{item.discovered_query}</strong>
                  <span>{item.discovery_count} discoveries</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {cmsOpen && <section className="queue"><div className="section-title"><div><span className="eyebrow">CONTENT CMS</span><h2>Books · Stories · History</h2></div><button className="approve" onClick={()=>document.getElementById("cms-upload").showModal()}>＋ Add content</button></div><div className="source-list">{contentItems.map(x=><article className="source" key={x.id}><div className="source-main"><div className="source-icon">▤</div><div className="source-copy"><div className="source-topline"><span className="provider">{x.content_type}</span><span className={`status ${x.status==="published"?"approved":"pending_review"}`}>{x.status}</span></div><h3>{x.title}</h3><div className="facts"><span>{x.language}</span><span>{x.rights_status}</span><span>{x.reading_minutes} min</span></div></div></div></article>)}</div><dialog id="cms-upload" className="cms-dialog"><form method="dialog"><button className="modal-close">×</button></form><span className="eyebrow">ADD READING CONTENT</span><h2>Upload complete content</h2><p>PDF, TXT or Markdown. Only upload works you have rights to host.</p><form onSubmit={async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const r=await apiFetch(`${API}/api/admin/content/upload`,{method:"POST",body:fd});const d=await r.json();if(!r.ok){setNotice(d.detail||"Upload failed");return}document.getElementById("cms-upload").close();setNotice("✓ Content uploaded, indexed and published");load()}} className="cms-form"><input name="title" placeholder="Title" required/><select name="content_type"><option value="book">Book</option><option value="story">Story</option><option value="history">History</option></select><input name="author" placeholder="Author"/><input name="language" defaultValue="English"/><input name="category" placeholder="Category"/><select name="rights_status"><option value="original">Original / my content</option><option value="public_domain">Public domain</option><option value="permission_granted">Permission granted</option><option value="licensed">Licensed</option></select><input name="rights_note" placeholder="Rights / edition note"/><textarea name="summary" placeholder="Summary"/><input name="file" type="file" accept=".pdf,.txt,.md" required/><input type="hidden" name="status" value="published"/><button className="approve">Upload, index & publish</button></form></dialog></section>}
        <section className="queue">
          <div className="section-title">
            <div>
              <span className="eyebrow">{filter === "pending_review" ? "DISCOVERED ON THE WEB" : "SOURCE REGISTRY"}</span>
              <h2>{sources.length} {filteredLabel.toLowerCase()}</h2>
            </div>
          </div>

          <div className="source-list">
            {sources.length === 0 && (
              <div className="empty">
                <div className="empty-orb">✦</div>
                <h3>Nothing here yet</h3>
                <p>Search Jain AI. Relevant new web sources will automatically appear in this queue.</p>
              </div>
            )}

            {sources.map((s) => (
              <article className="source" key={s.id}>
                <div className="source-main">
                  <div className="source-icon">
                    {s.source_type === "youtube" ? "▶" : "◉"}
                  </div>
                  <div className="source-copy">
                    <div className="source-topline">
                      <span className="provider">{(s.discovery_provider || s.source_type || "source").toUpperCase()}</span>
                      <span className={`status ${s.approval_status}`}>{s.approval_status?.replace("_", " ")}</span>
                    </div>
                    <h3>{s.title || host(s.url)}</h3>
                    <a href={s.url} target="_blank" rel="noreferrer">{host(s.url)} ↗</a>

                    <div className="facts">
                      {s.discovered_query && <span>Search: <b>{s.discovered_query}</b></span>}
                      <span>Seen <b>{s.discovery_count || 1}×</b></span>
                      {s.relevance_score != null && (
                        <span>Relevance <b>{Math.round(Number(s.relevance_score) * 100)}%</b></span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="actions">
                  <button className="ghost" onClick={() => setPreview(s)}>Preview</button>

                  {s.approval_status === "pending_review" && (
                    <>
                      <button
                        className="reject"
                        disabled={!!busy[s.id]}
                        onClick={() => act(s, "reject")}
                      >
                        Reject
                      </button>
                      <button
                        className="approve"
                        disabled={!!busy[s.id]}
                        onClick={() => act(s, "approve")}
                      >
                        {busy[s.id] === "approve" ? (
                          <><span className="spinner" /> Crawling & indexing…</>
                        ) : (
                          <>✓ Approve & Index</>
                        )}
                      </button>
                    </>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>

        {graph.length > 0 && (
          <section className="graph">
            <div className="section-title">
              <div>
                <span className="eyebrow">KNOWLEDGE GRAPH</span>
                <h2>Latest verified connections</h2>
              </div>
            </div>
            <div className="graph-grid">
              {graph.map((g) => (
                <div className="edge" key={g.id}>
                  <strong>{g.source}</strong>
                  <span>{g.relation?.replaceAll("_", " ")} →</span>
                  <strong>{g.target}</strong>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>

      {preview && (
        <div className="modal-backdrop" onClick={() => setPreview(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setPreview(null)}>×</button>
            <span className="eyebrow">SOURCE PREVIEW</span>
            <h2>{preview.title || host(preview.url)}</h2>
            <a href={preview.url} target="_blank" rel="noreferrer">{preview.url} ↗</a>
            <div className="preview-grid">
              <div><span>Provider</span><b>{preview.discovery_provider || preview.source_type}</b></div>
              <div><span>Discovery count</span><b>{preview.discovery_count || 1}</b></div>
              <div><span>Relevance</span><b>{Math.round(Number(preview.relevance_score || 0) * 100)}%</b></div>
              <div><span>Status</span><b>{preview.approval_status}</b></div>
            </div>
            <div className="query-box">
              <span>Discovered while answering</span>
              <strong>{preview.discovered_query || "Manual crawl"}</strong>
            </div>
            {preview.approval_status === "pending_review" && (
              <button className="approve modal-approve" onClick={() => { setPreview(null); act(preview, "approve"); }}>
                ✓ Approve, Crawl & Index
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, note }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);

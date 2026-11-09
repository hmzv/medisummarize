import { type FormEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, createRecord, listRecords, type RecordResponse } from "../api/client";
import { PrototypeShell } from "../components/PrototypeShell";
import { Icon } from "../components/Icon";

export function RecordsPage() {
  const navigate = useNavigate();
  const [records, setRecords] = useState<RecordResponse[]>([]);
  const [label, setLabel] = useState("");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("newest");
  const [creating, setCreating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  async function refresh() {
    setLoading(true); setError(null);
    try { setRecords(await listRecords()); }
    catch (err) { setError(err instanceof ApiError ? err.message : "Unable to load records. Check System status and try again."); }
    finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); }, []);
  async function onSubmit(event: FormEvent) {
    event.preventDefault(); if (!label.trim()) return;
    setError(null); setPending(true);
    try { const record = await createRecord(label.trim()); navigate(`/records/${record.id}`); }
    catch (err) { setError(err instanceof ApiError ? err.message : "Unable to create record. Try again."); }
    finally { setPending(false); }
  }
  const visible = records.filter(r => r.display_label.toLowerCase().includes(query.toLowerCase())).sort((a, b) => sort === "name" ? a.display_label.localeCompare(b.display_label) : Date.parse(b.created_at) - Date.parse(a.created_at));
  return <PrototypeShell><main className="workspace">
    <div className="page-heading"><div><h1>Record workspace</h1><p>Bring documents together. Review a summary with its sources.</p></div><button className="button primary" onClick={() => setCreating(!creating)} aria-expanded={creating}><Icon name="plus" />New record</button></div>
    {creating && <form className="create-form" onSubmit={onSubmit}><label htmlFor="record-label">Fictional case label<input id="record-label" autoFocus value={label} onChange={e => setLabel(e.target.value)} maxLength={120} required placeholder="e.g. Case A — longitudinal review" /></label><button className="button primary" disabled={pending || !label.trim()}>{pending ? "Creating…" : "Create record"}</button><button type="button" className="button" disabled={pending} onClick={() => setCreating(false)}>Cancel</button></form>}
    {error && <div className="error-message" role="alert">{error} <button className="text-button" onClick={() => void refresh()}>Retry</button></div>}
    <div className="workspace-intro"><div><h2>Your synthetic records</h2><p>One record per fictional patient. Access is limited to your account.</p></div><span className="count-label">{loading ? "Loading…" : `${records.length} record${records.length === 1 ? "" : "s"}`}</span></div>
    <div className="list-toolbar"><label className="search-field"><Icon name="search" /><input aria-label="Search records" placeholder="Search by case label…" value={query} onChange={e => setQuery(e.target.value)} /></label><label className="sort-field">Sort by<select value={sort} onChange={e => setSort(e.target.value)}><option value="newest">Newest first</option><option value="name">Case label</option></select></label></div>
    <div className="record-list" aria-busy={loading}>
      <div className="list-head"><span>Case record</span><span>Created</span><span>Open</span></div>
      {loading ? <p className="empty-state" role="status">Loading your records…</p> : visible.length ? visible.map(r => <Link className="record-row" to={`/records/${r.id}`} key={r.id}><span className="record-name"><span className="file-symbol"><Icon name="records" size={23} /></span><span><strong>{r.display_label}</strong><small>Synthetic patient record</small></span></span><time dateTime={r.created_at}>{new Date(r.created_at).toLocaleDateString("en-GB", {day:"numeric",month:"short",year:"numeric"})}</time><Icon name="arrow" /></Link>) : <div className="empty-state"><Icon name={query ? "search" : "records"} size={36} /><h3>{query ? "No matching records" : "Your first case starts here"}</h3><p>{query ? "Try another label or clear your search." : "Create a fictional case, then add lab reports, prescriptions, or discharge notes."}</p><button className="button" onClick={() => query ? setQuery("") : setCreating(true)}>{query ? "Clear search" : "Create your first record"}</button></div>}
    </div>
    <div className="workspace-help"><Icon name="book" /><div><h3>Preparing for the demonstration?</h3><p>Use the supplied synthetic cases to show extraction, missing information, and evidence review.</p></div><Link className="text-link" to="/guide">Open demo guide <Icon name="arrow" size={17} /></Link></div>
  </main></PrototypeShell>;
}

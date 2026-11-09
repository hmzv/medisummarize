import { type FormEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, deleteDocument, deleteRecord, downloadDocument, extractDocument, fetchExtractedText, fetchSummary, generateSummary, getRecord, listDocuments, uploadDocument, type DocumentResponse, type EvidencePassage, type ExtractedPageListResponse, type RecordResponse, type SummaryResponse } from "../api/client";
import { PrototypeShell } from "../components/PrototypeShell";
import { Icon } from "../components/Icon";
import { extractedPageAnchorId, SummaryReview } from "../components/SummaryReview";
import { ExperimentPreview } from "../components/ExperimentResults";
import { scrollToSource } from "../utils/sourceNavigation";

export function RecordDetailPage() {
  const { recordId } = useParams();
  const navigate = useNavigate();
  const input = useRef<HTMLInputElement>(null);
  const [record, setRecord] = useState<RecordResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [extracted, setExtracted] = useState<Record<string, ExtractedPageListResponse>>({});
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [tab, setTab] = useState("documents");
  const [dragging, setDragging] = useState(false);
  const [activePage, setActivePage] = useState("");
  const pending = !!busy;
  const waitingForExtraction = documents.some(d => d.status === "uploaded" || d.status === "processing");
  useEffect(() => {
    if (!recordId || !waitingForExtraction) return;
    let active = true;
    let attempts = 0;
    const timer = window.setInterval(() => {
      attempts += 1;
      if (attempts > 60) { window.clearInterval(timer); return; }
      void listDocuments(recordId).then(items => { if (active) setDocuments(items); }).catch(() => { /* The next scheduled check can recover a transient connection failure. */ });
    }, 2000);
    return () => { active = false; window.clearInterval(timer); };
  }, [recordId, waitingForExtraction]);
  useEffect(() => {
    let active = true;
    setRecord(null); setDocuments([]); setSummary(null); setExtracted({}); setError(null); setFiles([]); setNotice(""); setActivePage(""); setTab("documents");
    if (!recordId) return;
    void Promise.all([getRecord(recordId), listDocuments(recordId), fetchSummary(recordId).catch((err: unknown) => {
      if (err instanceof ApiError && err.status === 404) return null;
      throw err;
    })]).then(([r, docs, s]) => { if (active) { setRecord(r); setDocuments(docs); setSummary(s); } }).catch((err: unknown) => { if (active) setError(err instanceof ApiError ? err.message : "Unable to load this record. Return to Records and try again."); });
    return () => { active = false; };
  }, [recordId]);
  async function act(label: string, action: () => Promise<void>) {
    setBusy(label); setError(null); setNotice("");
    try { await action(); }
    catch (err) { setError(err instanceof ApiError ? err.message : `${label} failed. Check your connection and try again.`); }
    finally { setBusy(""); }
  }
  function selectFiles(selected: File[]) {
    setFiles(selected); setError(null);
    if (selected.some(f => !/\.(pdf|png|jpe?g|txt)$/i.test(f.name))) {
      setError("Choose PDF, PNG, JPEG, or UTF-8 text files."); setFiles([]);
    }
  }
  async function onUpload(event: FormEvent) {
    event.preventDefault(); if (!recordId || !files.length) return;
    await act("Uploading documents", async () => {
      // Remove successful files immediately so retrying a partial batch cannot duplicate them.
      for (const file of files) {
        await uploadDocument(recordId, file);
        setFiles(current => current.filter(f => f !== file));
        setSummary(null); setNotice("Documents changed. Generate a new summary after checking the extracted text.");
        setDocuments(await listDocuments(recordId));
      }
      if (input.current) input.current.value = "";
    });
  }
  async function showText(id: string) {
    if (!recordId) return;
    await act("Loading extracted text", async () => { const result = await fetchExtractedText(recordId, id); setExtracted(current => ({ ...current, [id]: result })); });
  }
  async function openSource(passage: EvidencePassage) {
    if (!recordId) return;
    await act("Opening source", async () => {
      const result = await fetchExtractedText(recordId, passage.document_id);
      setExtracted(current => ({ ...current, [passage.document_id]: result }));
      setActivePage(extractedPageAnchorId(passage.document_id, passage.page)); setTab("documents");
    });
  }
  useEffect(() => { if (activePage && tab === "documents") scrollToSource(activePage); }, [activePage, extracted, tab]);
  const processed = documents.filter(d => ["extracted", "indexed", "ready"].includes(d.status)).length;
  return <PrototypeShell><main className="workspace record-detail">
    <Link to="/records" className="text-link back-link">All records</Link>
    {error && <p className="error-message" role="alert">{error}</p>}
    {!record ? <p role="status">{error ? "This record is unavailable." : "Loading record…"}</p> : <>
      <div className="page-heading"><div><h1>Review the record</h1><p className="record-caption"><strong>{record.display_label}</strong><span className="status-label synthetic">Synthetic demo</span></p></div><div className="record-primary-actions"><button className="button primary" disabled={pending} onClick={() => { setTab("documents"); window.setTimeout(() => input.current?.focus(), 0); }}><Icon name="upload" />Upload documents</button><button className="button" disabled={pending || !processed} onClick={() => void act("Generating summary", async () => { setSummary(await generateSummary(record.id)); setTab("summary"); })}><Icon name="activity" />{busy === "Generating summary" ? "Generating…" : summary ? "Regenerate summary" : "Generate summary"}</button></div></div>
      {tab === "documents" && <ol className="workflow-steps" aria-label="Review workflow"><li data-complete={documents.length > 0}><span>1</span>Add documents <small>{documents.length} uploaded</small></li><li data-complete={processed > 0}><span>2</span>Review extracted text <small>{processed} ready</small></li><li data-complete={!!summary}><span>3</span>Verify summary <small>{summary ? "Ready for review" : "Awaiting generation"}</small></li></ol>}
      {!processed && documents.length > 0 && <p className="notice">Extract text from at least one document to enable summary generation.</p>}
      {busy && <p className="working-status" role="status"><span className="busy-dot" />{busy}… {busy === "Generating summary" && "This may take up to two minutes."}</p>}
      {notice && <p className="notice" role="status">{notice}</p>}
      <div className="tabs" role="tablist" aria-label="Record views">{["documents", "summary"].map(t => <button key={t} id={`tab-${t}`} role="tab" aria-selected={tab === t} aria-controls={`panel-${t}`} tabIndex={tab === t ? 0 : -1} onKeyDown={e => { if (e.key === "ArrowLeft" || e.key === "ArrowRight") { e.preventDefault(); const next = t === "documents" ? "summary" : "documents"; setTab(next); document.getElementById(`tab-${next}`)?.focus(); } }} onClick={() => setTab(t)}>{t === "documents" ? `Documents (${documents.length})` : "Summary & evidence"}</button>)}</div>
      <section role="tabpanel" id="panel-documents" aria-labelledby="tab-documents" hidden={tab !== "documents"}>
        <form className={`upload-zone ${dragging ? "dragging" : ""}`} onSubmit={e => void onUpload(e)} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); if (!pending) selectFiles(Array.from(e.dataTransfer.files)); }}>
          <Icon name="upload" size={30} /><h2>Add source documents</h2><p>Drop files here, or choose files below. PDF, PNG, JPEG, and UTF-8 text.</p><label className="file-picker">Choose synthetic files<input ref={input} aria-label="Choose synthetic files" type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.txt" disabled={pending} onChange={e => selectFiles(Array.from(e.target.files ?? []))} /></label>
          {files.length > 0 && <><ul className="selected-files">{files.map((f, i) => <li key={`${f.name}-${i}`}>{f.name} <small>({(f.size / 1024).toFixed(1)} KB)</small></li>)}</ul><button className="button primary" disabled={pending}>Upload {files.length} file{files.length === 1 ? "" : "s"}</button></>}
        </form>
        <div className="section-heading"><h2>Source documents</h2><p>Check extracted text against the original before reviewing a summary.</p></div>
        {!documents.length ? <div className="document-empty"><Icon name="file" size={30} /><p>No documents yet. Add the files for this fictional case above.</p></div> : <ul className="document-list">{documents.map(doc => <li key={doc.id}>
          <div className="document-heading"><span className="file-symbol"><Icon name="file" /></span><div className="document-title"><h3>{doc.original_filename}</h3><p>{doc.file_kind.toUpperCase()} · {(doc.size_bytes / 1024).toFixed(1)} KB {doc.page_count ? `· ${doc.page_count} page${doc.page_count === 1 ? "" : "s"}` : ""}</p></div><span className={`status-label ${["extracted", "indexed", "ready"].includes(doc.status) ? "ready" : ""}`}>{["extracted", "indexed", "ready"].includes(doc.status) ? "Text ready" : doc.status.replaceAll("_", " ")}</span></div>
          {doc.public_error && <p className="error-message">{doc.public_error}</p>}
          <div className="document-actions"><button className="button small" disabled={pending} onClick={() => void act("Downloading original", () => downloadDocument(record.id, doc))}>Original</button><button className="button small" disabled={pending} onClick={() => void act("Extracting text", async () => { const result = await extractDocument(record.id, doc.id); setExtracted(current => ({...current, [doc.id]: result})); setDocuments(await listDocuments(record.id)); setSummary(null); setNotice("Text changed. Generate a new summary when your review is complete."); })}>Extract text</button><button className="button small" disabled={pending || !["extracted", "indexed", "ready"].includes(doc.status)} aria-expanded={!!extracted[doc.id]} onClick={() => extracted[doc.id] ? setExtracted(current => { const next = {...current}; delete next[doc.id]; return next; }) : void showText(doc.id)}>{extracted[doc.id] ? "Hide text" : "Review text"}</button><button className="text-button danger" disabled={pending} onClick={() => { if (window.confirm(`Delete ${doc.original_filename}? Its extracted text and current summary will be removed.`)) void act("Deleting document", async () => { await deleteDocument(record.id, doc.id); setDocuments(await listDocuments(record.id)); setExtracted(current => { const next = {...current}; delete next[doc.id]; return next; }); setSummary(null); setNotice("Document removed. Generate a fresh summary from the remaining sources."); }); }}>Delete</button></div>
          {extracted[doc.id] && <div className="extracted-text">{!extracted[doc.id].items.length && <p>No text available. Try extracting again or use a clearer source.</p>}{extracted[doc.id].items.map(page => <div key={page.id} id={extractedPageAnchorId(doc.id, page.page_number)} className={activePage === extractedPageAnchorId(doc.id, page.page_number) ? "source-page active-page" : "source-page"}><h4>Page {page.page_number}<span>{page.extraction_method}{page.ocr_confidence !== null ? ` · OCR confidence ${page.ocr_confidence.toFixed(0)}` : ""}</span></h4>{page.warnings.map(w => <p className="notice" key={w}>{w}</p>)}<pre>{page.text || "No text on this page."}</pre></div>)}</div>}
        </li>)}</ul>}
      </section>
      <section role="tabpanel" id="panel-summary" aria-labelledby="tab-summary" hidden={tab !== "summary"}>
        {!!documents.length && <div className="document-strip" aria-label="Source documents">{documents.map(doc => <button className="document-selector" key={doc.id} onClick={() => void openSource({id: doc.id, document_id: doc.id, original_filename: doc.original_filename, page: 1, method: "source", text: ""})}><Icon name="file" size={23} /><strong>{doc.original_filename}</strong><span className={`status-label ${["extracted", "indexed", "ready"].includes(doc.status) ? "ready" : ""}`}>{["extracted", "indexed", "ready"].includes(doc.status) ? "Extracted" : "Needs review"}</span>{doc.page_count && <small>{doc.page_count} page{doc.page_count === 1 ? "" : "s"}</small>}</button>)}</div>}
        {summary ? <SummaryReview key={summary.id} summary={summary} recordLabel={record.display_label} onOpenSource={p => void openSource(p)} /> : <div className="empty-state"><Icon name="activity" size={36} /><h2>Your summary will appear here</h2><p>Add documents and review their text, then choose Generate summary.</p></div>}
        {tab === "summary" && <ExperimentPreview />}
      </section>
      <details className="record-management"><summary>Record management</summary><p>Deleting this record permanently removes its source documents and generated summaries.</p><button className="button danger" disabled={pending} onClick={() => { if (window.confirm("Permanently delete this fictional record and all its files?")) void act("Deleting record", async () => { await deleteRecord(record.id); navigate("/records"); }); }}>Delete record</button></details>
    </>}
  </main></PrototypeShell>;
}

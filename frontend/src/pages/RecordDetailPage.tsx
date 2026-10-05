import { type FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ApiError,
  deleteDocument,
  deleteRecord,
  downloadDocument,
  extractDocument,
  fetchExtractedText,
  fetchSummary,
  generateSummary,
  getRecord,
  listDocuments,
  uploadDocument,
  type DocumentResponse,
  type EvidencePassage,
  type ExtractedPageListResponse,
  type RecordResponse,
  type SummaryResponse,
} from "../api/client";
import { PrototypeShell } from "../components/PrototypeShell";
import {
  extractedPageAnchorId,
  SummaryReview,
} from "../components/SummaryReview";

export function RecordDetailPage() {
  const { recordId } = useParams();
  const navigate = useNavigate();
  const [record, setRecord] = useState<RecordResponse | null>(null);
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [extracted, setExtracted] = useState<Record<string, ExtractedPageListResponse>>({});
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  async function refreshDocuments(id: string) {
    const items = await listDocuments(id);
    setDocuments(items);
  }

  useEffect(() => {
    if (!recordId) {
      return;
    }
    void getRecord(recordId)
      .then(async (current) => {
        setRecord(current);
        await refreshDocuments(current.id);
        try {
          setSummary(await fetchSummary(current.id));
        } catch (err) {
          if (!(err instanceof ApiError && err.status === 404)) {
            throw err;
          }
        }
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Unable to load record.");
      });
  }, [recordId]);

  async function onGenerateSummary() {
    if (!recordId) {
      return;
    }
    setPending(true);
    setError(null);
    try {
      const result = await generateSummary(recordId);
      setSummary(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to generate a summary.");
    } finally {
      setPending(false);
    }
  }

  async function onOpenSource(passage: EvidencePassage) {
    if (!recordId) {
      return;
    }
    try {
      if (!extracted[passage.document_id]) {
        const result = await fetchExtractedText(recordId, passage.document_id);
        setExtracted((current) => ({ ...current, [passage.document_id]: result }));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load extracted text.");
      return;
    }
    window.setTimeout(() => {
      window.document
        .getElementById(extractedPageAnchorId(passage.document_id, passage.page))
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 50);
  }

  async function onDelete() {
    if (!recordId) {
      return;
    }
    const confirmed = window.confirm(
      "Delete this synthetic record container and its files? This cannot be undone.",
    );
    if (!confirmed) {
      return;
    }
    setPending(true);
    try {
      await deleteRecord(recordId);
      navigate("/records");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to delete record.");
      setPending(false);
    }
  }

  async function onUpload(event: FormEvent) {
    event.preventDefault();
    if (!recordId || !file) {
      return;
    }
    setError(null);
    setPending(true);
    try {
      await uploadDocument(recordId, file);
      setFile(null);
      await refreshDocuments(recordId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to upload the file.");
    } finally {
      setPending(false);
    }
  }

  async function onExtract(documentId: string) {
    if (!recordId) {
      return;
    }
    setPending(true);
    setError(null);
    try {
      const result = await extractDocument(recordId, documentId);
      setExtracted((current) => ({ ...current, [documentId]: result }));
      await refreshDocuments(recordId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Extraction failed.");
    } finally {
      setPending(false);
    }
  }

  async function onShowExtracted(documentId: string) {
    if (!recordId) {
      return;
    }
    try {
      const result = await fetchExtractedText(recordId, documentId);
      setExtracted((current) => ({ ...current, [documentId]: result }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load extracted text.");
    }
  }

  async function onDeleteDocument(documentId: string) {
    if (!recordId) {
      return;
    }
    setPending(true);
    setError(null);
    try {
      await deleteDocument(recordId, documentId);
      await refreshDocuments(recordId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to delete the document.");
    } finally {
      setPending(false);
    }
  }

  return (
    <PrototypeShell>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <p className="text-sm">
          <Link to="/records" className="text-accent-dark hover:underline">
            ← All records
          </Link>
        </p>
        {error ? <p className="mt-4 text-sm text-red-800">{error}</p> : null}
        {record ? (
          <>
            <section className="mt-6 rounded-lg border border-line bg-card p-6">
              <p className="text-xs font-semibold uppercase tracking-wide text-accent">
                Synthetic container
              </p>
              <h1 className="mt-2 text-2xl font-semibold">{record.display_label}</h1>
              <p className="mt-2 text-sm text-muted">{record.synthetic_notice}</p>
              <dl className="mt-4 space-y-1 text-sm text-muted">
                <div>Opaque ID: {record.id}</div>
                <div>Created: {new Date(record.created_at).toLocaleString()}</div>
              </dl>
            </section>
            <section className="mt-6 rounded-lg border border-line bg-card p-6">
              <h2 className="text-lg font-semibold">Documents</h2>
              <p className="mt-1 text-sm text-muted">
                PDF, PNG, JPEG, or UTF-8 text. The server checks file content, not
                the browser MIME type. Original files are stored outside the web
                root and are only downloadable by the owner. Upload files from{" "}
                <code>data/synthetic/</code> for the labeled demo cases.
              </p>
              <form className="mt-4 flex flex-col gap-3 sm:flex-row" onSubmit={(event) => void onUpload(event)}>
                <input
                  className="flex-1 text-sm"
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,.txt,application/pdf,image/png,image/jpeg,text/plain"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                  required
                />
                <button
                  type="submit"
                  disabled={pending || !file}
                  className="rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-dark disabled:opacity-60"
                >
                  {pending ? "Working…" : "Upload"}
                </button>
              </form>
              <ul className="mt-6 divide-y divide-line rounded border border-line">
                {documents.length === 0 ? (
                  <li className="px-4 py-4 text-sm text-muted">No documents uploaded.</li>
                ) : (
                  documents.map((doc) => (
                    <li key={doc.id} className="flex flex-col gap-3 px-4 py-3">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="font-medium">{doc.original_filename}</p>
                        <p className="text-xs text-muted">
                          {doc.file_kind} · {doc.status} · {doc.size_bytes} bytes
                          {doc.page_count ? ` · ${doc.page_count} page(s)` : ""}
                        </p>
                        {doc.public_error ? (
                          <p className="text-xs text-red-800">{doc.public_error}</p>
                        ) : null}
                      </div>
                      <div className="flex flex-wrap gap-2 text-sm">
                        <button
                          type="button"
                          className="rounded border border-line px-3 py-1 hover:bg-paper"
                          onClick={() => void downloadDocument(record.id, doc).catch((err: unknown) => {
                            setError(err instanceof ApiError ? err.message : "Download failed.");
                          })}
                        >
                          Original
                        </button>
                        <button
                          type="button"
                          className="rounded border border-line px-3 py-1 hover:bg-paper"
                          disabled={pending}
                          onClick={() => void onExtract(doc.id)}
                        >
                          Extract text
                        </button>
                        <button
                          type="button"
                          className="rounded border border-line px-3 py-1 hover:bg-paper"
                          onClick={() => void onShowExtracted(doc.id)}
                        >
                          Review text
                        </button>
                        <button
                          type="button"
                          className="rounded border border-red-800 px-3 py-1 text-red-800 hover:bg-red-50"
                          disabled={pending}
                          onClick={() => void onDeleteDocument(doc.id)}
                        >
                          Delete
                        </button>
                      </div>
                      </div>
                      {extracted[doc.id] ? (
                        <div className="rounded border border-line bg-paper p-3 text-sm">
                          <p className="text-xs text-muted">
                            Status: {extracted[doc.id].status}
                            {extracted[doc.id].public_error
                              ? ` · ${extracted[doc.id].public_error}`
                              : ""}
                          </p>
                          {extracted[doc.id].items.map((page) => (
                            <div
                              key={page.id}
                              id={extractedPageAnchorId(doc.id, page.page_number)}
                              className="mt-2"
                            >
                              <p className="text-xs font-semibold text-accent-dark">
                                Page {page.page_number} · {page.extraction_method}
                                {page.ocr_confidence !== null
                                  ? ` · OCR confidence ${page.ocr_confidence.toFixed(0)}`
                                  : ""}
                              </p>
                              {page.warnings.map((warning) => (
                                <p key={warning} className="text-xs text-red-800">
                                  {warning}
                                </p>
                              ))}
                              <pre className="mt-1 whitespace-pre-wrap font-sans text-sm text-ink">
                                {page.text || "(no text)"}
                              </pre>
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </li>
                  ))
                )}
              </ul>
            </section>
            <section className="mt-6 rounded-lg border border-line bg-card p-6">
              <h2 className="text-lg font-semibold">Structured summary</h2>
              <p className="mt-1 text-sm text-muted">
                Retrieval is limited to this record. Click a citation to highlight
                the retrieved passage and scroll toward the matching extracted page.
              </p>
              <button
                type="button"
                className="mt-4 rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-dark disabled:opacity-60"
                disabled={pending}
                onClick={() => void onGenerateSummary()}
              >
                {pending ? "Working…" : "Generate summary"}
              </button>
              {summary ? <SummaryReview summary={summary} onOpenSource={(passage) => void onOpenSource(passage)} /> : null}
            </section>
            <button
              type="button"
              onClick={() => void onDelete()}
              disabled={pending}
              className="mt-6 rounded border border-red-800 px-4 py-2 text-sm text-red-800 hover:bg-red-50 disabled:opacity-60"
            >
              {pending ? "Deleting…" : "Delete record"}
            </button>
          </>
        ) : error ? null : (
          <p className="mt-6 text-sm text-muted">Loading record…</p>
        )}
      </main>
    </PrototypeShell>
  );
}

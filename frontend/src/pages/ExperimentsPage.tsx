import { useEffect, useRef, useState, type ChangeEvent } from "react";
import { ApiError } from "../api/client";
import { importExperiments, listExperiments, type ExperimentRun } from "../api/experiments";
import { ExperimentTable, percent } from "../components/ExperimentResults";
import { PrototypeShell } from "../components/PrototypeShell";
import { Icon } from "../components/Icon";

export function ExperimentsPage() {
  const [runs, setRuns] = useState<ExperimentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [split, setSplit] = useState("all");
  const [model, setModel] = useState("all");
  const picker = useRef<HTMLInputElement>(null);
  async function refresh() {
    setLoading(true); setError("");
    try { setRuns((await listExperiments()).items); }
    catch (err) { setError(err instanceof ApiError ? err.message : "Unable to load results. Check the backend and retry."); }
    finally { setLoading(false); }
  }
  useEffect(() => { void refresh(); }, []);
  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]; if (!file) return;
    setError(""); setNotice(""); setBusy(true);
    try {
      if (file.size > 1_000_000) throw new Error("Choose an aggregate JSON file smaller than 1 MB, not predictions or model weights.");
      let body: unknown;
      try { body = JSON.parse(await file.text()); } catch { throw new Error("This file is not valid JSON. Export experiment-results.json from the notebook."); }
      const result = await importExperiments(body);
      setRuns((await listExperiments()).items); setNotice(`Imported ${result.items.length} result${result.items.length === 1 ? "" : "s"}. Measurements remain user-supplied.`);
    } catch (err) { setError(err instanceof Error ? err.message : "Import failed. Check the JSON export and try again."); }
    finally { setBusy(false); if (picker.current) picker.current.value = ""; }
  }
  const visible = runs.filter(run => (split === "all" || run.split === split) && (model === "all" || run.model === model));
  return <PrototypeShell><main className="workspace experiments-page"><div className="page-heading"><div><h1>Experiments</h1><p>Compare measured results. Keep the evidence behind every score.</p></div><button className="button primary" disabled={busy} onClick={() => picker.current?.click()}><Icon name="upload" />{busy ? "Importing…" : "Import results"}</button><input ref={picker} className="sr-only" type="file" accept=".json,application/json" aria-label="Import experiment JSON" onChange={e => void upload(e)} /></div>
    {error && <div className="error-message" role="alert">{error} <button className="text-button" onClick={() => void refresh()}>Retry loading</button></div>}{notice && <p className="success-message" role="status">{notice}</p>}
    <div className="experiment-intro"><Icon name="experiments" size={28} /><div><h2>Handwritten word recognition</h2><p>RxHandBD v3 · Tesseract → pretrained TrOCR-small → fine-tuned TrOCR-small</p><p className="text-muted">This experiment evaluates cropped words. Whole handwritten reports need a separate layout and full-page evaluation.</p></div></div>
    <div className="results-toolbar"><label>Evaluation split<select value={split} onChange={e => setSplit(e.target.value)}><option value="all">All splits</option><option value="validation">Validation</option><option value="test">Final test</option></select></label><label>Model<select value={model} onChange={e => setModel(e.target.value)}><option value="all">All models</option>{Array.from(new Set(runs.map(run => run.model))).map(name => <option key={name}>{name}</option>)}</select></label><button className="text-button" onClick={() => void refresh()} disabled={loading}>Refresh results</button></div>
    {loading ? <p className="empty-state" role="status">Loading experiment results…</p> : <ExperimentTable runs={visible} planned={split === "all" && model === "all"} />}
    {!loading && !runs.length && <div className="results-empty"><h2>Ready for your first measured run</h2><p>Run the handwriting notebook in Kaggle, download experiment-results.json, and import it here. Planned models above have no scores until a run is imported.</p></div>}
    <div className="metric-notes"><p><strong>CER ↓</strong> is the proportion of character edits needed to match the label; lower is better. <strong>Exact match ↑</strong> is the share of crops read perfectly; higher is better.</p><p>Scores are imported by your account and have not been independently verified. Compare models on the same dataset, split, and preprocessing. Validation scores guide development; final test scores assess the frozen experiment.</p></div>
    {visible.length > 0 && <section className="run-details"><h2>Run evidence</h2>{visible.map(run => <details key={run.id}><summary>{run.model} · {run.split} · {new Date(run.created_at).toLocaleString()}</summary><dl><div><dt>Word error rate</dt><dd>{percent(run.metrics.wer)}</dd></div><div><dt>Digit sequence match</dt><dd>{run.metrics.digit_sequence_match === null ? "No digit labels" : `${percent(run.metrics.digit_sequence_match)} across ${run.metrics.digit_samples} crops`}</dd></div><div><dt>Duration</dt><dd>{run.elapsed_seconds.toFixed(1)} seconds</dd></div></dl><ul>{run.limitations.map(item => <li key={item}>{item}</li>)}</ul><details className="provenance-details"><summary>Reproduction metadata</summary><pre>{JSON.stringify(run.provenance, null, 2)}</pre></details></details>)}</section>}
  </main></PrototypeShell>;
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listExperiments, type ExperimentRun } from "../api/experiments";
import { Icon } from "./Icon";

export const PLANNED_MODELS = ["Tesseract", "Pretrained TrOCR-small", "Fine-tuned TrOCR-small"];
export const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

export function ExperimentTable({ runs, planned = true }: { runs: ExperimentRun[]; planned?: boolean }) {
  const pending = planned ? PLANNED_MODELS.filter(model => !runs.some(run => run.model === model)) : [];
  return <div className="table-scroll" tabIndex={0} aria-label="Scrollable experiment results"><table className="results-table"><thead><tr><th scope="col">Model</th><th scope="col">Dataset</th><th scope="col">Status / split</th><th scope="col">CER <span className="metric-direction">↓</span></th><th scope="col">Exact match <span className="metric-direction">↑</span></th></tr></thead><tbody>
    {runs.map(run => <tr key={run.id}><th scope="row">{run.model}<small>{run.samples.toLocaleString()} crops</small></th><td>{run.dataset}</td><td><span className="status-label imported">Imported · {run.split}</span></td><td className="numeric">{percent(run.metrics.cer)}</td><td className="numeric">{percent(run.metrics.exact_match)}</td></tr>)}
    {pending.map(model => <tr key={model}><th scope="row">{model}</th><td>RxHandBD v3</td><td><span className="status-label neutral">Not run</span></td><td className="numeric">—</td><td className="numeric">—</td></tr>)}
    {!runs.length && !pending.length && <tr><td colSpan={5}>No results match this filter. Choose another split or model.</td></tr>}
  </tbody></table></div>;
}

export function ExperimentPreview() {
  const [runs, setRuns] = useState<ExperimentRun[]>([]);
  const [failed, setFailed] = useState(false);
  useEffect(() => { let active = true; void listExperiments().then(result => { if (active) setRuns(result.items.slice(0, 3)); }).catch(() => { if (active) setFailed(true); }); return () => { active = false; }; }, []);
  return <section className="experiment-preview" aria-labelledby="experiment-preview-title"><div className="experiment-heading"><div><h2 id="experiment-preview-title">Experiment runs</h2><p>Training runs in Kaggle. Import results after evaluation.</p></div><Link className="text-link" to="/experiments">View experiments <Icon name="arrow" size={18} /></Link></div>{failed ? <p className="notice">Experiment results could not be loaded. Open Experiments to retry.</p> : <ExperimentTable runs={runs} />}{runs.length > 0 && <p className="result-provenance">Imported measurements · Keep validation and final test results separate.</p>}</section>;
}

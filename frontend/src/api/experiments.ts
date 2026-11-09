import { fetchJson } from "./client";

export type ExperimentRun = {
  id: string;
  model: string;
  dataset: string;
  split: "validation" | "test";
  samples: number;
  metrics: { cer: number; wer: number; exact_match: number; digit_sequence_match: number | null; digit_samples: number };
  elapsed_seconds: number;
  created_at: string;
  limitations: string[];
  verification: "user_supplied";
  provenance: Record<string, unknown>;
};
type ResultList = { items: ExperimentRun[]; notice: string };
export const listExperiments = () => fetchJson<ResultList>("/api/v1/experiments");
export const importExperiments = (body: unknown) => fetchJson<ResultList>("/api/v1/experiments/import", {method: "POST", body});

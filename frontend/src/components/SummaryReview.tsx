import { useState } from "react";
import type { Claim, EvidencePassage, SummaryResponse } from "../api/client";

export function evidenceAnchorId(passageId: string): string {
  return `evidence-${passageId}`;
}

export function extractedPageAnchorId(documentId: string, page: number): string {
  return `extracted-page-${documentId}-${page}`;
}

type SummaryReviewProps = {
  summary: SummaryResponse;
  onOpenSource?: (passage: EvidencePassage) => void;
};

const CLAIM_SECTIONS: Array<[string, (summary: SummaryResponse) => Claim[]]> = [
  ["Key history", (item) => item.summary.key_history],
  ["Current documented findings", (item) => item.summary.current_documented_findings],
  ["Medications", (item) => item.summary.medications],
  ["Allergies", (item) => item.summary.allergies],
  ["Laboratory findings", (item) => item.summary.laboratory_findings],
];

export function SummaryReview({ summary, onOpenSource }: SummaryReviewProps) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const byId = new Map(summary.evidence.map((item) => [item.id, item]));

  function goToEvidence(passageId: string) {
    setActiveId(passageId);
    const passage = byId.get(passageId);
    if (passage) {
      onOpenSource?.(passage);
    }
    window.document.getElementById(evidenceAnchorId(passageId))?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }

  return (
    <div className="mt-4 grid gap-4 lg:grid-cols-2">
      <div className="space-y-3 text-sm">
        {summary.is_mock ? (
          <p className="font-semibold text-red-800">
            MOCK/TEST OUTPUT — not a real-model result. Do not use in evaluation
            metrics.
          </p>
        ) : null}
        {summary.validation_warnings.map((warning) => (
          <p key={warning} className="text-xs text-red-800">
            {warning}
          </p>
        ))}
        {CLAIM_SECTIONS.map(([label, read]) => {
          const claims = read(summary);
          return (
            <div key={label}>
              <h3 className="font-semibold">{label}</h3>
              {claims.length === 0 ? (
                <p className="text-muted">None stated.</p>
              ) : (
                claims.map((claim) => (
                  <ClaimRow
                    key={`${label}-${claim.text}`}
                    claim={claim}
                    onCite={goToEvidence}
                  />
                ))
              )}
            </div>
          );
        })}
        <div>
          <h3 className="font-semibold">Unresolved or unavailable</h3>
          <ul className="list-disc px-5">
            {summary.summary.unresolved_or_unavailable.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        {summary.summary.processing_limitations.length > 0 ? (
          <div>
            <h3 className="font-semibold">Processing limitations</h3>
            <ul className="list-disc px-5">
              {summary.summary.processing_limitations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
        <p className="text-xs text-muted">{summary.summary.disclaimer}</p>
      </div>
      <aside className="rounded border border-line bg-paper p-4 text-sm">
        <h3 className="font-semibold">Evidence passages</h3>
        <p className="mt-1 text-xs text-muted">
          Citation IDs mean a source was attached. They are not clinical proof.
          Click a citation to scroll here.
        </p>
        {summary.evidence.length === 0 ? (
          <p className="mt-3 text-muted">No passages were retrieved.</p>
        ) : (
          <ul className="mt-3 space-y-3">
            {summary.evidence.map((passage) => {
              const selected = passage.id === activeId;
              return (
                <li
                  key={passage.id}
                  id={evidenceAnchorId(passage.id)}
                  data-testid={`evidence-${passage.id}`}
                  data-active={selected ? "true" : "false"}
                  className={`rounded border p-3 ${
                    selected ? "border-accent bg-card" : "border-line bg-card"
                  }`}
                >
                  <p className="text-xs font-semibold text-accent-dark">
                    {passage.original_filename} · page {passage.page} ·{" "}
                    {passage.method}
                  </p>
                  <p className="mt-1 whitespace-pre-wrap">{passage.text}</p>
                  <p className="mt-2 font-mono text-[11px] text-muted">{passage.id}</p>
                </li>
              );
            })}
          </ul>
        )}
      </aside>
    </div>
  );
}

function ClaimRow({
  claim,
  onCite,
}: {
  claim: Claim;
  onCite: (passageId: string) => void;
}) {
  return (
    <p className="mt-1">
      <span>{claim.text} </span>
      <span className="text-xs text-muted">[{claim.evidence_status}</span>
      {claim.source_ids.length === 0 ? (
        <span className="text-xs text-muted">: none]</span>
      ) : (
        <>
          <span className="text-xs text-muted">: </span>
          {claim.source_ids.map((sourceId, index) => (
            <span key={sourceId}>
              {index > 0 ? <span className="text-xs text-muted">, </span> : null}
              <button
                type="button"
                className="text-xs text-accent-dark underline"
                onClick={() => onCite(sourceId)}
              >
                {sourceId.slice(0, 8)}
              </button>
            </span>
          ))}
          <span className="text-xs text-muted">]</span>
        </>
      )}
    </p>
  );
}

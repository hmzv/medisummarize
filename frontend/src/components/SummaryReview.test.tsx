import { fireEvent, render, screen } from "@testing-library/react";
import { SummaryReview } from "./SummaryReview";
import type { SummaryResponse } from "../api/client";

const summary: SummaryResponse = {
  id: "sum-1",
  record_id: "rec-1",
  summary: {
    key_history: [
      {
        text: "MOCK/TEST OUTPUT: Cited passage begins: denied chest pain.",
        source_ids: ["chunk-abc-1"],
        evidence_status: "citation_present",
      },
    ],
    current_documented_findings: [],
    medications: [],
    allergies: [],
    laboratory_findings: [],
    unresolved_or_unavailable: ["MOCK/TEST OUTPUT: labeled mock generation."],
    processing_limitations: ["Generation provider is MOCK/TEST OUTPUT."],
    disclaimer: "Research prototype for clinical-document summarization only.",
  },
  evidence: [
    {
      id: "chunk-abc-1",
      document_id: "doc-1",
      original_filename: "discharge.txt",
      page: 1,
      method: "utf8_text",
      text: "The patient denied chest pain.",
    },
  ],
  prompt_version: "summarize-v1",
  generation_provider: "mock",
  generation_model: "mock-test-v1",
  embedding_model: "test-hash-v1",
  is_mock: true,
  validation_warnings: ["MOCK/TEST OUTPUT: this summary is not a real-model result."],
  created_at: "2026-10-05T00:00:00Z",
};

describe("SummaryReview", () => {
  afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
  it.each([[false, "smooth"], [true, "auto"]] as const)("scrolls to the cited passage with reduced motion %s", (reducedMotion, behavior) => {
    vi.stubGlobal("matchMedia", vi.fn(() => ({matches: reducedMotion})));
    const onOpenSource = vi.fn();
    const scroll = vi.fn();
    const original = window.document.getElementById.bind(window.document);
    vi.spyOn(window.document, "getElementById").mockImplementation((id: string) => {
      const node = original(id);
      if (node) {
        Object.defineProperty(node, "scrollIntoView", { value: scroll, configurable: true });
      }
      return node;
    });

    render(<SummaryReview summary={summary} onOpenSource={onOpenSource} />);
    fireEvent.click(screen.getByRole("button", { name: "chunk-ab" }));

    expect(screen.getByTestId("evidence-chunk-abc-1")).toHaveAttribute("data-active", "true");
    expect(scroll).toHaveBeenCalledWith({behavior, block:"center"});
    expect(onOpenSource).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Open source page" }));
    expect(onOpenSource).toHaveBeenCalledWith(summary.evidence[0]);
  });
});

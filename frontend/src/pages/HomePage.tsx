import { BackendStatus } from "../components/BackendStatus";
import { DisclaimerBanner } from "../components/DisclaimerBanner";

export function HomePage() {
  return (
    <div className="min-h-screen">
      <DisclaimerBanner />
      <header className="border-b border-line bg-card">
        <div className="mx-auto flex max-w-5xl items-baseline justify-between px-4 py-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-accent">
              FYP-I research prototype
            </p>
            <h1 className="mt-1 text-2xl font-semibold text-ink">
              MediSummarize AI
            </h1>
          </div>
          <p className="hidden text-sm text-muted sm:block">
            Segment 1 · Foundation
          </p>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <p className="max-w-3xl text-base leading-relaxed text-muted">
          This prototype will help a reviewer upload synthetic clinical
          documents, retrieve supporting passages, and inspect a structured
          summary. Authentication and the RAG pipeline are not enabled yet.
        </p>
        <div className="mt-8">
          <BackendStatus />
        </div>
      </main>
    </div>
  );
}

import { type FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, createRecord, listRecords, type RecordResponse } from "../api/client";
import { PrototypeShell } from "../components/PrototypeShell";

export function RecordsPage() {
  const [records, setRecords] = useState<RecordResponse[]>([]);
  const [label, setLabel] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function refresh() {
    const items = await listRecords();
    setRecords(items);
  }

  useEffect(() => {
    void refresh().catch((err: unknown) => {
      setError(err instanceof ApiError ? err.message : "Unable to load records.");
    });
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      await createRecord(label);
      setLabel("");
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to create record.");
    } finally {
      setPending(false);
    }
  }

  return (
    <PrototypeShell>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <h1 className="text-2xl font-semibold">Synthetic records</h1>
        <p className="mt-2 max-w-3xl text-sm text-muted">
          Each record is a container for documents associated with one fictional
          case. Do not use real names, CNICs, phone numbers, or other identifying
          fields.
        </p>
        <form className="mt-6 flex flex-col gap-3 sm:flex-row" onSubmit={onSubmit}>
          <input
            className="flex-1 rounded border border-line bg-card px-3 py-2"
            placeholder="Fictional display label, e.g. Case A — longitudinal demo"
            value={label}
            onChange={(event) => setLabel(event.target.value)}
            required
            maxLength={120}
          />
          <button
            type="submit"
            disabled={pending}
            className="rounded bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-dark disabled:opacity-60"
          >
            {pending ? "Creating…" : "Create record"}
          </button>
        </form>
        {error ? <p className="mt-3 text-sm text-red-800">{error}</p> : null}
        <ul className="mt-8 divide-y divide-line rounded-lg border border-line bg-card">
          {records.length === 0 ? (
            <li className="px-4 py-6 text-sm text-muted">No records yet.</li>
          ) : (
            records.map((record) => (
              <li key={record.id} className="px-4 py-4">
                <Link
                  to={`/records/${record.id}`}
                  className="font-medium text-accent-dark hover:underline"
                >
                  {record.display_label}
                </Link>
                <p className="mt-1 text-xs text-muted">{record.synthetic_notice}</p>
              </li>
            ))
          )}
        </ul>
      </main>
    </PrototypeShell>
  );
}

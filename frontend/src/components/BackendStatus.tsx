import { useEffect, useState } from "react";
import {
  checkBackendConnection,
  type BackendConnection,
} from "../api/client";

type BackendStatusProps = {
  check?: () => Promise<BackendConnection>;
};

export function BackendStatus({
  check = checkBackendConnection,
}: BackendStatusProps) {
  const [connection, setConnection] = useState<BackendConnection>({
    state: "checking",
  });

  useEffect(() => {
    let cancelled = false;
    void check().then((result) => {
      if (!cancelled) {
        setConnection(result);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [check]);

  return (
    <section
      aria-live="polite"
      className="rounded-lg border border-line bg-card p-6 shadow-sm"
    >
      <h2 className="text-lg font-semibold text-ink">Backend connection</h2>
      <p className="mt-1 text-sm text-muted">
        The frontend calls <code>/api/v1/health</code> and{" "}
        <code>/api/v1/health/ready</code>. Start the FastAPI server on port 8000
        for a successful check.
      </p>
      <dl className="mt-4 grid gap-2 text-sm">
        <StatusRows connection={connection} />
      </dl>
    </section>
  );
}

function StatusRows({ connection }: { connection: BackendConnection }) {
  if (connection.state === "checking") {
    return (
      <div className="text-muted" data-testid="backend-status">
        Checking backend…
      </div>
    );
  }

  if (connection.state === "disconnected") {
    return (
      <div data-testid="backend-status">
        <p className="font-medium text-red-800">Disconnected</p>
        <p className="mt-1 text-muted">{connection.message}</p>
      </div>
    );
  }

  const databaseLabel =
    connection.ready?.database === "connected"
      ? "Connected"
      : "API up; database check failed or not ready";

  return (
    <div data-testid="backend-status">
      <p className="font-medium text-accent-dark">Connected</p>
      <p className="mt-2 text-muted">
        Service: {connection.health.service} · Environment:{" "}
        {connection.health.environment}
      </p>
      <p className="text-muted">Database: {databaseLabel}</p>
    </div>
  );
}

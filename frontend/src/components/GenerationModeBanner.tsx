import { useEffect, useState } from "react";
import {
  fetchGenerationHealth,
  type GenerationHealthResponse,
} from "../api/client";

type GenerationModeBannerProps = {
  load?: () => Promise<GenerationHealthResponse>;
};

export function GenerationModeBanner({
  load = fetchGenerationHealth,
}: GenerationModeBannerProps) {
  const [health, setHealth] = useState<GenerationHealthResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    void load()
      .then((result) => {
        if (!cancelled) {
          setHealth(result);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setHealth(null);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [load]);

  if (!health) {
    return null;
  }

  if (health.is_mock) {
    return (
      <div
        role="status"
        data-testid="generation-mode-banner"
        className="border-b border-red-800 bg-red-50 px-4 py-2 text-sm text-red-800"
      >
        <p className="mx-auto max-w-5xl font-medium">
          MOCK/TEST OUTPUT is enabled ({health.provider}). Generated text is not a
          real-model result and must not be used in evaluation metrics.
        </p>
      </div>
    );
  }

  return (
    <div
      role="status"
      data-testid="generation-mode-banner"
      className="border-b border-line bg-paper px-4 py-2 text-sm text-muted"
    >
      <p className="mx-auto max-w-5xl">
        Generation provider: {health.provider}
        {health.status !== "ok" ? ` · status ${health.status}` : ""}
        {health.warning ? ` · ${health.warning}` : ""}
      </p>
    </div>
  );
}

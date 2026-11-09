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
        className="mode-banner"
      >
        <details><summary>Mock generation · Verify output against sources</summary><p>
          MOCK/TEST OUTPUT is enabled ({health.provider}). Generated text is not a
          real-model result and must not be used in evaluation metrics.
        </p></details>
      </div>
    );
  }

  return (
    <div
      role="status"
      data-testid="generation-mode-banner"
      className="mode-banner"
    >
      <p className="mx-auto max-w-5xl">
        Generation provider: {health.provider}
        {health.status !== "ok" ? ` · status ${health.status}` : ""}
        {health.warning ? ` · ${health.warning}` : ""}
      </p>
    </div>
  );
}

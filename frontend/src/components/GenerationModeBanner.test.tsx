import { render, screen } from "@testing-library/react";
import { GenerationModeBanner } from "./GenerationModeBanner";
import type { GenerationHealthResponse } from "../api/client";

describe("GenerationModeBanner", () => {
  it("labels mock generation so it cannot be mistaken for a real model", async () => {
    const load = async (): Promise<GenerationHealthResponse> => ({
      status: "ok",
      provider: "mock",
      is_mock: true,
      warning: "MOCK/TEST OUTPUT is enabled.",
    });

    render(<GenerationModeBanner load={load} />);
    expect(await screen.findByTestId("generation-mode-banner")).toHaveTextContent(
      /MOCK\/TEST OUTPUT is enabled \(mock\)/i,
    );
  });

  it("shows the configured real provider name", async () => {
    const load = async (): Promise<GenerationHealthResponse> => ({
      status: "ok",
      provider: "openai_compatible",
      is_mock: false,
      warning: null,
    });

    render(<GenerationModeBanner load={load} />);
    expect(await screen.findByTestId("generation-mode-banner")).toHaveTextContent(
      "Generation provider: openai_compatible",
    );
  });
});

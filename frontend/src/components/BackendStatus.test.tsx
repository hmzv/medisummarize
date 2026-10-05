import { render, screen } from "@testing-library/react";
import { BackendStatus } from "./BackendStatus";
import type { BackendConnection } from "../api/client";

describe("BackendStatus", () => {
  it("reports a connected backend", async () => {
    const check = async (): Promise<BackendConnection> => ({
      state: "connected",
      health: {
        status: "ok",
        service: "medisummarize-ai",
        environment: "test",
      },
      ready: { status: "ready", database: "connected" },
    });

    render(<BackendStatus check={check} />);
    expect(await screen.findByText("Connected")).toBeInTheDocument();
    expect(screen.getByText(/Environment: test/)).toBeInTheDocument();
    expect(screen.getByText(/Database: Connected/)).toBeInTheDocument();
  });

  it("reports a disconnected backend", async () => {
    const check = async (): Promise<BackendConnection> => ({
      state: "disconnected",
      message: "Backend is not reachable.",
    });

    render(<BackendStatus check={check} />);
    expect(await screen.findByText("Disconnected")).toBeInTheDocument();
    expect(screen.getByText("Backend is not reachable.")).toBeInTheDocument();
  });
});

import "@testing-library/jest-dom/vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "../src/App";

const projection = {
  lens: "value_stream",
  context: {
    industry: { selected: "Generic Services", available: ["Generic Services"] },
    journey: { selected: "LBGUPS Customer Lifecycle", available: ["LBGUPS Customer Lifecycle"] }
  },
  archimate_legend: [{ type: "Application Component", description: "Application support." }],
  lanes: [{ id: "stage.buy", name: "Buy", archimate_type: "Value Stream", node_ids: ["process.qualify_opportunity"] }],
  nodes: [{
    id: "process.qualify_opportunity",
    name: "Qualify Opportunity",
    type: "process",
    archimate_type: "Business Process",
    verification_state: "inferred",
    review_state: "candidate",
    evidence_ids: [],
    confidence: 0.72
  }],
  edges: [],
  process_contexts: {
    "process.qualify_opportunity": {
      performed_by: [],
      applications: [],
      data: { reads: [], creates: [], updates: [], deletes: [] },
      capabilities: [],
      value_streams: [],
      gates: [],
      pain_points: [],
      evidence_ids: [],
      confidence: { score: 0.72, rationale: "Graph relationship confidence." }
    }
  },
  overlays: [],
  unresolved: [],
  collapsible_branches: []
};

describe("App", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loads the selected Milky Way projection through the API proxy", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => projection
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...projection, lens: "organization" })
      } as Response);

    render(<App />);

    expect(await screen.findByText("Generic Services")).toBeInTheDocument();
    expect(screen.getByText("LBGUPS Customer Lifecycle")).toBeInTheDocument();
    expect(screen.getByText("Business Process")).toBeInTheDocument();
    expect(screen.getByText("Who does this process?")).toBeInTheDocument();
    expect(screen.getByText("What application supports it?")).toBeInTheDocument();
    expect(screen.getByText("What data is used, created, or modified?")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Organization Lens" }));

    expect(await screen.findByText("Generic Services")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/api/views/milky-way?lens=organization");
  });

  it("shows a retry path when the Milky Way request fails", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockRejectedValueOnce(new Error("API unavailable"))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => projection
      } as Response);

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to load the Milky Way.");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByText("Generic Services")).toBeInTheDocument();
  });
});

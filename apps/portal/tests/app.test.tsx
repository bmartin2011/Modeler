import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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
    cleanup();
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
        json: async () => ({ items: [] })
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
        json: async () => ({ items: [] })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => projection
      } as Response);

    render(<App />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to load the Milky Way.");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByText("Generic Services")).toBeInTheDocument();
  });

  it("sends a simple question and renders the API answer", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => projection
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [] })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          question: "Where are approval gates concentrated?",
          answer: "Operations Review Gate is a likely concentration point.",
          known: ["Onboard Customer", "Deliver Service"],
          unknown: ["Approval volume and average wait time are not modeled."],
          evidence_ids: ["evidence.seed_org"],
          confidence: { score: 0.68, rationale: "Multiple modeled value streams require the same gate." },
          next_best_question: "How often does this gate block work for more than one business day?"
        })
      } as Response);

    render(<App />);

    await screen.findByText("Generic Services");
    fireEvent.change(screen.getByLabelText("Ask a model question"), {
      target: { value: "Where are approval gates concentrated?" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    expect(await screen.findByText("Operations Review Gate is a likely concentration point.")).toBeInTheDocument();
    expect(screen.getByText("68% confidence")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/api/questions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "Where are approval gates concentrated?" })
    });
  });

  it("records a correction against the current answer", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => projection
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [] })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          rating: "correction",
          comment: "Priya owns delivery but does not report to John.",
          creates_learning_signal: true,
          review_state: "pending"
        })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [{
            id: "feedback.1",
            target_id: "answer.Who_reports_to_John",
            rating: "correction",
            comment: "Priya owns delivery but does not report to John.",
            creates_learning_signal: true,
            review_state: "pending"
          }]
        })
      } as Response);

    render(<App />);

    await screen.findByText("Generic Services");
    fireEvent.click(screen.getByRole("button", { name: "thumbs down" }));
    fireEvent.change(screen.getByLabelText("Correction"), {
      target: { value: "Priya owns delivery but does not report to John." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Record correction" }));

    expect(await screen.findByText("Learning signal captured")).toBeInTheDocument();
    expect(await screen.findByText("Priya owns delivery but does not report to John.")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_id: "answer.Who_reports_to_John",
        rating: "correction",
        comment: "Priya owns delivery but does not report to John."
      })
    });
    expect(fetch).toHaveBeenCalledWith("/api/review-queue");
  });

  it("accepts a correction from the review queue", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce({
        ok: true,
        json: async () => projection
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [{
            id: "feedback.1",
            target_id: "answer.Who_reports_to_John",
            rating: "correction",
            comment: "Priya owns delivery but does not report to John.",
            creates_learning_signal: true,
            review_state: "pending"
          }]
        })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          rating: "correction",
          comment: "Priya owns delivery but does not report to John.",
          creates_learning_signal: true,
          review_state: "accepted"
        })
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [{
            id: "feedback.1",
            target_id: "answer.Who_reports_to_John",
            rating: "correction",
            comment: "Priya owns delivery but does not report to John.",
            creates_learning_signal: true,
            review_state: "accepted"
          }]
        })
      } as Response);

    render(<App />);

    await screen.findByText("Priya owns delivery but does not report to John.");
    fireEvent.click(screen.getByRole("button", { name: "Accept" }));

    expect(await screen.findByText("accepted")).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith("/api/review-queue/feedback.1/decision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_state: "accepted" })
    });
  });
});

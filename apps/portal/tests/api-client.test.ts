import { afterEach, describe, expect, it, vi } from "vitest";
import {
  askQuestion,
  decideReviewQueueItem,
  getMilkyWay,
  getReviewQueue,
  previewReviewQueueItem,
  recordFeedback
} from "../src/api/client";

describe("portal API client", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("requests Milky Way views through the portal API proxy", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ lens: "value_stream", sectors: [] })
    } as Response);

    await getMilkyWay("value_stream");

    expect(fetch).toHaveBeenCalledWith("/api/views/milky-way?lens=value_stream");
  });

  it("raises a useful error when the API returns a non-OK response", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 502,
      statusText: "Bad Gateway"
    } as Response);

    await expect(getMilkyWay("organization")).rejects.toThrow(
      "Modeler API request failed: 502 Bad Gateway"
    );
  });

  it("posts questions through the portal API proxy", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        question: "Who reports to John?",
        answer: "Maya and Luis are verified direct reports.",
        known: ["Maya reports to John."],
        unknown: ["Priya is unresolved."],
        evidence_ids: ["evidence.seed_org"],
        confidence: { score: 0.86, rationale: "Two verified relationships." },
        next_best_question: "Should Priya be modeled as reporting to John?"
      })
    } as Response);

    const answer = await askQuestion("Who reports to John?");

    expect(answer.answer).toContain("Maya and Luis");
    expect(fetch).toHaveBeenCalledWith("/api/questions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: "Who reports to John?" })
    });
  });

  it("raises a useful error when a question request fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error"
    } as Response);

    await expect(askQuestion("What is unsupported?")).rejects.toThrow(
      "Modeler API request failed: 500 Internal Server Error"
    );
  });

  it("posts feedback through the portal API proxy", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "feedback.1",
        target_id: "answer.Who_reports_to_John",
        rating: "thumbs_up",
        comment: "Useful answer.",
        creates_learning_signal: true
      })
    } as Response);

    const event = await recordFeedback({
      target_id: "answer.Who_reports_to_John",
      rating: "thumbs_up",
      comment: "Useful answer."
    });

    expect(event.creates_learning_signal).toBe(true);
    expect(fetch).toHaveBeenCalledWith("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_id: "answer.Who_reports_to_John",
        rating: "thumbs_up",
        comment: "Useful answer."
      })
    });
  });

  it("raises a useful error when feedback recording fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 503,
      statusText: "Service Unavailable"
    } as Response);

    await expect(recordFeedback({
      target_id: "answer.Who_reports_to_John",
      rating: "thumbs_down",
      comment: "Missing evidence."
    })).rejects.toThrow("Modeler API request failed: 503 Service Unavailable");
  });

  it("loads the review queue through the portal API proxy", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [{
          id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          rating: "correction",
          comment: "Priya owns delivery but does not report to John.",
          creates_learning_signal: true
        }]
      })
    } as Response);

    const queue = await getReviewQueue();

    expect(queue.items[0].comment).toBe("Priya owns delivery but does not report to John.");
    expect(fetch).toHaveBeenCalledWith("/api/review-queue");
  });

  it("raises a useful error when review queue loading fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 504,
      statusText: "Gateway Timeout"
    } as Response);

    await expect(getReviewQueue()).rejects.toThrow(
      "Modeler API request failed: 504 Gateway Timeout"
    );
  });

  it("posts review decisions through the portal API proxy", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "feedback.1",
        target_id: "answer.Who_reports_to_John",
        rating: "correction",
        comment: "Priya owns delivery but does not report to John.",
        creates_learning_signal: true,
        review_state: "accepted"
      })
    } as Response);

    const item = await decideReviewQueueItem("feedback.1", "accepted");

    expect(item.review_state).toBe("accepted");
    expect(fetch).toHaveBeenCalledWith("/api/review-queue/feedback.1/decision", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_state: "accepted" })
    });
  });

  it("loads review promotion previews through the portal API proxy", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({
        before: {
          question: "Who reports to John?",
          answer: "Maya and Luis are verified direct reports to John. Priya is associated with John, but the reporting relationship is unresolved.",
          known: ["Maya reports to John.", "Luis reports to John."],
          unknown: ["Priya is associated with John, but the reporting relationship is unresolved."],
          evidence_ids: ["evidence.seed_org"],
          confidence: { score: 0.86, rationale: "Two verified relationships." },
          next_best_question: "Should Priya be modeled as reporting to John?",
          learning_trace: []
        },
        proposed: {
          question: "Who reports to John?",
          answer: "Maya and Luis are verified direct reports to John.",
          known: [
            "Maya reports to John.",
            "Luis reports to John.",
            "Priya owns delivery but does not report to John."
          ],
          unknown: ["No unresolved association with John is modeled."],
          evidence_ids: ["evidence.seed_org"],
          confidence: { score: 0.86, rationale: "Two verified relationships." },
          next_best_question: null,
          learning_trace: [{
            feedback_id: "feedback.1",
            target_id: "answer.Who_reports_to_John",
            comment: "Priya owns delivery but does not report to John.",
            review_state: "accepted"
          }]
        },
        added_known: ["Priya owns delivery but does not report to John."],
        removed_unknown: ["Priya is associated with John, but the reporting relationship is unresolved."],
        learning_trace: [{
          feedback_id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          comment: "Priya owns delivery but does not report to John.",
          review_state: "accepted"
        }]
      })
    } as Response);

    const preview = await previewReviewQueueItem("feedback.1");

    expect(preview.added_known).toEqual(["Priya owns delivery but does not report to John."]);
    expect(fetch).toHaveBeenCalledWith("/api/review-queue/feedback.1/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" }
    });
  });

  it("raises a useful error when review decision recording fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: false,
      status: 404,
      statusText: "Not Found"
    } as Response);

    await expect(decideReviewQueueItem("feedback.missing", "rejected")).rejects.toThrow(
      "Modeler API request failed: 404 Not Found"
    );
  });
});

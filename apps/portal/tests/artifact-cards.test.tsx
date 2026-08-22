import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PromotionPreview } from "../src/api/client";
import { ArtifactCards } from "../src/components/ArtifactCards";

const promotionPreview: PromotionPreview = {
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
};

describe("ArtifactCards", () => {
  afterEach(() => {
    cleanup();
  });

  it("shows recorded feedback in the review queue", () => {
    render(
      <ArtifactCards
        reviewQueueItems={[{
          id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          rating: "correction",
          comment: "Priya owns delivery but does not report to John.",
          creates_learning_signal: true,
          review_state: "pending"
        }]}
        onDecideReviewItem={async () => undefined}
        onPreviewReviewItem={async () => promotionPreview}
      />
    );

    expect(screen.getByText("Review Queue")).toBeInTheDocument();
    expect(screen.getByText("Priya owns delivery but does not report to John.")).toBeInTheDocument();
    expect(screen.getByText("Learning signal")).toBeInTheDocument();
  });

  it("shows an empty queue state when no feedback is waiting", () => {
    render(
      <ArtifactCards
        reviewQueueItems={[]}
        onDecideReviewItem={async () => undefined}
        onPreviewReviewItem={async () => promotionPreview}
      />
    );

    expect(screen.getByText("No feedback waiting for review.")).toBeInTheDocument();
  });

  it("accepts pending review queue items", async () => {
    const onDecideReviewItem = vi.fn().mockResolvedValue(undefined);
    render(
      <ArtifactCards
        reviewQueueItems={[{
          id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          rating: "correction",
          comment: "Priya owns delivery but does not report to John.",
          creates_learning_signal: true,
          review_state: "pending"
        }]}
        onDecideReviewItem={onDecideReviewItem}
        onPreviewReviewItem={async () => promotionPreview}
      />
    );

    screen.getByRole("button", { name: "Accept" }).click();

    expect(onDecideReviewItem).toHaveBeenCalledWith("feedback.1", "accepted");
  });

  it("previews pending review queue promotion impact", async () => {
    const onPreviewReviewItem = vi.fn().mockResolvedValue(promotionPreview);
    render(
      <ArtifactCards
        reviewQueueItems={[{
          id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          rating: "correction",
          comment: "Priya owns delivery but does not report to John.",
          creates_learning_signal: true,
          review_state: "pending"
        }]}
        onDecideReviewItem={async () => undefined}
        onPreviewReviewItem={onPreviewReviewItem}
      />
    );

    screen.getByRole("button", { name: "Preview" }).click();

    expect(onPreviewReviewItem).toHaveBeenCalledWith("feedback.1");
    expect(await screen.findByText("Promotion Preview")).toBeInTheDocument();
    expect(screen.getByText("Known fact added")).toBeInTheDocument();
    expect(screen.getByText("Priya owns delivery but does not report to John.")).toBeInTheDocument();
    expect(screen.getByText("Unknown removed")).toBeInTheDocument();
  });

  it("shows a preview loading state and prevents duplicate preview requests", async () => {
    const onPreviewReviewItem = vi.fn(() => new Promise<PromotionPreview>(() => undefined));
    render(
      <ArtifactCards
        reviewQueueItems={[{
          id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          rating: "correction",
          comment: "Priya owns delivery but does not report to John.",
          creates_learning_signal: true,
          review_state: "pending"
        }]}
        onDecideReviewItem={async () => undefined}
        onPreviewReviewItem={onPreviewReviewItem}
      />
    );

    const previewButton = screen.getByRole("button", { name: "Preview" });
    fireEvent.click(previewButton);
    fireEvent.click(previewButton);

    expect(onPreviewReviewItem).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Previewing..." })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Accept" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Reject" })).toBeDisabled();
  });

  it("shows an inline error when preview fails and keeps the item pending", async () => {
    const onPreviewReviewItem = vi.fn().mockRejectedValue(new Error("Preview unavailable"));
    render(
      <ArtifactCards
        reviewQueueItems={[{
          id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          rating: "correction",
          comment: "Priya owns delivery but does not report to John.",
          creates_learning_signal: true,
          review_state: "pending"
        }]}
        onDecideReviewItem={async () => undefined}
        onPreviewReviewItem={onPreviewReviewItem}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Preview" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to preview feedback.");
    expect(screen.getByText("pending")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Accept" })).toBeEnabled();
  });

  it("shows an accept loading state and prevents duplicate decision requests", async () => {
    const onDecideReviewItem = vi.fn(() => new Promise<void>(() => undefined));
    render(
      <ArtifactCards
        reviewQueueItems={[{
          id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          rating: "correction",
          comment: "Priya owns delivery but does not report to John.",
          creates_learning_signal: true,
          review_state: "pending"
        }]}
        onDecideReviewItem={onDecideReviewItem}
        onPreviewReviewItem={async () => promotionPreview}
      />
    );

    const acceptButton = screen.getByRole("button", { name: "Accept" });
    fireEvent.click(acceptButton);
    fireEvent.click(acceptButton);

    expect(onDecideReviewItem).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Accepting..." })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Preview" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Reject" })).toBeDisabled();
  });

  it("shows an inline error when a review decision fails", async () => {
    const onDecideReviewItem = vi.fn().mockRejectedValue(new Error("Decision failed"));
    render(
      <ArtifactCards
        reviewQueueItems={[{
          id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          rating: "correction",
          comment: "Priya owns delivery but does not report to John.",
          creates_learning_signal: true,
          review_state: "pending"
        }]}
        onDecideReviewItem={onDecideReviewItem}
        onPreviewReviewItem={async () => promotionPreview}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Accept" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to record review decision.");
    expect(screen.getByText("pending")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: "Accept" })).toBeEnabled());
  });

  it("shows reviewed queue item status without decision buttons", () => {
    render(
      <ArtifactCards
        reviewQueueItems={[{
          id: "feedback.1",
          target_id: "answer.Who_reports_to_John",
          rating: "correction",
          comment: "Priya owns delivery but does not report to John.",
          creates_learning_signal: true,
          review_state: "accepted"
        }]}
        onDecideReviewItem={async () => undefined}
        onPreviewReviewItem={async () => promotionPreview}
      />
    );

    expect(screen.getByText("accepted")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Accept" })).not.toBeInTheDocument();
  });
});

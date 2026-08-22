import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { FeedbackControls } from "../src/components/FeedbackControls";

describe("FeedbackControls", () => {
  afterEach(() => {
    cleanup();
  });

  it("records thumbs up feedback for the current answer", async () => {
    const onRecordFeedback = vi.fn().mockResolvedValue({
      id: "feedback.1",
      target_id: "answer.Who_reports_to_John",
      rating: "thumbs_up",
      comment: "Helpful.",
      creates_learning_signal: true
    });

    render(
      <FeedbackControls
        targetId="answer.Who_reports_to_John"
        onRecordFeedback={onRecordFeedback}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "thumbs up" }));

    expect(await screen.findByText("Feedback recorded")).toBeInTheDocument();
    expect(onRecordFeedback).toHaveBeenCalledWith({
      target_id: "answer.Who_reports_to_John",
      rating: "thumbs_up",
      comment: "Helpful answer."
    });
  });

  it("records a correction from thumbs down feedback", async () => {
    const onRecordFeedback = vi.fn().mockResolvedValue({
      id: "feedback.2",
      target_id: "answer.Who_reports_to_John",
      rating: "correction",
      comment: "Priya owns delivery but does not report to John.",
      creates_learning_signal: true
    });

    render(
      <FeedbackControls
        targetId="answer.Who_reports_to_John"
        onRecordFeedback={onRecordFeedback}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "thumbs down" }));
    fireEvent.change(screen.getByLabelText("Correction"), {
      target: { value: "Priya owns delivery but does not report to John." }
    });
    fireEvent.click(screen.getByRole("button", { name: "Record correction" }));

    expect(await screen.findByText("Feedback recorded")).toBeInTheDocument();
    expect(screen.getByText("Learning signal captured")).toBeInTheDocument();
    expect(onRecordFeedback).toHaveBeenCalledWith({
      target_id: "answer.Who_reports_to_John",
      rating: "correction",
      comment: "Priya owns delivery but does not report to John."
    });
  });

  it("shows feedback recording failures", async () => {
    const onRecordFeedback = vi.fn().mockRejectedValue(new Error("API unavailable"));

    render(
      <FeedbackControls
        targetId="answer.Who_reports_to_John"
        onRecordFeedback={onRecordFeedback}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "thumbs up" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to record feedback.");
  });
});

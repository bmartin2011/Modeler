import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { QuestionPanel } from "../src/components/QuestionPanel";

describe("QuestionPanel", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders answer confidence and next best question", () => {
    render(
      <QuestionPanel
        answer={{
          question: "Who reports to John?",
          answer: "Maya and Luis are verified direct reports.",
          known: ["Maya reports to John."],
          unknown: ["Priya is unresolved."],
          evidence_ids: ["evidence.seed_org"],
          confidence: { score: 0.86, rationale: "Two verified relationships." },
          next_best_question: "Should Priya be modeled as reporting to John?"
        }}
        onAskQuestion={async () => undefined}
      />
    );

    expect(screen.getByText("Maya and Luis are verified direct reports.")).toBeInTheDocument();
    expect(screen.getByText("86% confidence")).toBeInTheDocument();
    expect(screen.getByText("Should Priya be modeled as reporting to John?")).toBeInTheDocument();
  });

  it("renders learning traces for accepted feedback", () => {
    render(
      <QuestionPanel
        answer={{
          question: "Who reports to John?",
          answer: "Maya and Luis are verified direct reports.",
          known: ["Priya owns delivery but does not report to John."],
          unknown: [],
          evidence_ids: ["evidence.seed_org"],
          confidence: { score: 0.86, rationale: "Two verified relationships." },
          next_best_question: null,
          learning_trace: [
            {
              feedback_id: "feedback.1",
              target_id: "answer.Who_reports_to_John",
              comment: "Priya owns delivery but does not report to John.",
              review_state: "accepted"
            }
          ]
        }}
        onAskQuestion={async () => undefined}
      />
    );

    expect(screen.getByText("Learned from accepted feedback")).toBeInTheDocument();
    expect(screen.getByText("feedback.1")).toBeInTheDocument();
    expect(screen.getByText("Priya owns delivery but does not report to John.")).toBeInTheDocument();
  });

  it("submits typed questions", async () => {
    const onAskQuestion = vi.fn().mockResolvedValue(undefined);
    render(
      <QuestionPanel
        answer={{
          question: "Who reports to John?",
          answer: "Maya and Luis are verified direct reports.",
          known: [],
          unknown: [],
          evidence_ids: [],
          confidence: { score: 0.86, rationale: "Two verified relationships." },
          next_best_question: null
        }}
        onAskQuestion={onAskQuestion}
      />
    );

    fireEvent.change(screen.getByLabelText("Ask a model question"), {
      target: { value: "Where are approval gates concentrated?" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    expect(onAskQuestion).toHaveBeenCalledWith("Where are approval gates concentrated?");
  });

  it("does not submit blank questions", () => {
    const onAskQuestion = vi.fn();
    render(
      <QuestionPanel
        answer={{
          question: "Who reports to John?",
          answer: "Maya and Luis are verified direct reports.",
          known: [],
          unknown: [],
          evidence_ids: [],
          confidence: { score: 0.86, rationale: "Two verified relationships." },
          next_best_question: null
        }}
        onAskQuestion={onAskQuestion}
      />
    );

    fireEvent.change(screen.getByLabelText("Ask a model question"), {
      target: { value: "   " }
    });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    expect(onAskQuestion).not.toHaveBeenCalled();
  });

  it("shows question submission failures", async () => {
    const onAskQuestion = vi.fn().mockRejectedValue(new Error("API unavailable"));
    render(
      <QuestionPanel
        answer={{
          question: "Who reports to John?",
          answer: "Maya and Luis are verified direct reports.",
          known: [],
          unknown: [],
          evidence_ids: [],
          confidence: { score: 0.86, rationale: "Two verified relationships." },
          next_best_question: null
        }}
        onAskQuestion={onAskQuestion}
      />
    );

    fireEvent.change(screen.getByLabelText("Ask a model question"), {
      target: { value: "Where are approval gates concentrated?" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Unable to answer that question.");
  });
});

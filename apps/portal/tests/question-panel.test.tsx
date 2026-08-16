import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { QuestionPanel } from "../src/components/QuestionPanel";

describe("QuestionPanel", () => {
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
      />
    );

    expect(screen.getByText("Maya and Luis are verified direct reports.")).toBeInTheDocument();
    expect(screen.getByText("86% confidence")).toBeInTheDocument();
    expect(screen.getByText("Should Priya be modeled as reporting to John?")).toBeInTheDocument();
  });
});

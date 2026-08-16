import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MilkyWayMap } from "../src/components/MilkyWayMap";

describe("MilkyWayMap", () => {
  it("renders sectors and confidence overlays", () => {
    render(
      <MilkyWayMap
        projection={{
          lens: "value_stream",
          sectors: [{ id: "vs.onboard", name: "Onboard Customer", rings: ["capability", "gate"] }],
          overlays: [{ type: "risk", label: "Approval gate concentration", confidence: 0.68 }],
          collapsible_branches: []
        }}
      />
    );

    expect(screen.getByText("Onboard Customer")).toBeInTheDocument();
    expect(screen.getByText("Approval gate concentration")).toBeInTheDocument();
    expect(screen.getByText("68% confidence")).toBeInTheDocument();
  });
});

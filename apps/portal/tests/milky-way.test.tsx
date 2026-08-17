import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MilkyWayMap } from "../src/components/MilkyWayMap";

const projection = {
  lens: "value_stream",
  context: {
    industry: { selected: "Generic Services", available: ["Generic Services"] },
    journey: { selected: "LBGUPS Customer Lifecycle", available: ["LBGUPS Customer Lifecycle"] }
  },
  archimate_legend: [
    { type: "Business Process", description: "Business behavior." },
    { type: "Application Component", description: "Application support." },
    { type: "Data Object", description: "Business data." }
  ],
  lanes: [
    { id: "stage.buy", name: "Buy", archimate_type: "Value Stream", node_ids: ["process.qualify_opportunity"] }
  ],
  nodes: [
    {
      id: "process.qualify_opportunity",
      name: "Qualify Opportunity",
      type: "process",
      archimate_type: "Business Process",
      verification_state: "inferred",
      review_state: "candidate",
      evidence_ids: ["evidence.seed_process_web"],
      confidence: 0.72
    }
  ],
  edges: [],
  process_contexts: {
    "process.qualify_opportunity": {
      performed_by: [{ id: "role.sales_lead", name: "Sales Lead", archimate_type: "Business Role" }],
      applications: [{ id: "app.crm", name: "CRM", archimate_type: "Application Component" }],
      data: {
        reads: [{ id: "data.lead_profile", name: "Lead Profile", archimate_type: "Data Object" }],
        creates: [{ id: "data.qualified_opportunity", name: "Qualified Opportunity", archimate_type: "Data Object" }],
        updates: [],
        deletes: []
      },
      capabilities: [{ id: "cap.opportunity_management", name: "Opportunity Management", archimate_type: "Capability" }],
      value_streams: [{ id: "stage.buy", name: "Buy", archimate_type: "Value Stream" }],
      gates: [],
      pain_points: [],
      evidence_ids: ["evidence.seed_process_web"],
      confidence: { score: 0.72, rationale: "Average confidence across graph relationships for this process." }
    }
  },
  overlays: [],
  unresolved: [{ entity_id: "person.priya", question: "Should Priya be modeled as reporting to John?" }],
  collapsible_branches: []
};

describe("MilkyWayMap", () => {
  it("renders graph-derived ArchiMate Galaxy context", () => {
    render(<MilkyWayMap projection={projection} />);

    expect(screen.getByText("Generic Services")).toBeInTheDocument();
    expect(screen.getByText("LBGUPS Customer Lifecycle")).toBeInTheDocument();
    expect(screen.getAllByText("Buy").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Qualify Opportunity").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Business Process").length).toBeGreaterThan(0);
    expect(screen.getByText("Who does this process?")).toBeInTheDocument();
    expect(screen.getByText("Sales Lead")).toBeInTheDocument();
    expect(screen.getByText("What application supports it?")).toBeInTheDocument();
    expect(screen.getByText("CRM")).toBeInTheDocument();
    expect(screen.getByText("What data is used, created, or modified?")).toBeInTheDocument();
    expect(screen.getByText("Lead Profile")).toBeInTheDocument();
    expect(screen.getByText("Qualified Opportunity")).toBeInTheDocument();
    expect(screen.getByText("Should Priya be modeled as reporting to John?")).toBeInTheDocument();
  });
});

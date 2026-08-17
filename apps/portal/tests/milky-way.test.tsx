import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
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
        updates: [{ id: "data.opportunity_record", name: "Opportunity Record", archimate_type: "Data Object" }],
        deletes: [{ id: "data.stale_lead", name: "Stale Lead", archimate_type: "Data Object" }]
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

const projectionWithSecondProcess = {
  ...projection,
  lanes: [{
    ...projection.lanes[0],
    node_ids: ["process.qualify_opportunity", "process.onboard_customer"]
  }],
  nodes: [
    ...projection.nodes,
    {
      id: "process.onboard_customer",
      name: "Onboard Customer",
      type: "process",
      archimate_type: "Business Process",
      verification_state: "verified",
      review_state: "accepted",
      evidence_ids: ["evidence.onboarding"],
      confidence: 0.91
    }
  ],
  process_contexts: {
    ...projection.process_contexts,
    "process.onboard_customer": {
      performed_by: [{ id: "role.onboarding_specialist", name: "Onboarding Specialist", archimate_type: "Business Role" }],
      applications: [{ id: "app.customer_portal", name: "Customer Portal", archimate_type: "Application Component" }],
      data: { reads: [], creates: [], updates: [], deletes: [] },
      capabilities: [{ id: "cap.customer_onboarding", name: "Customer Onboarding", archimate_type: "Capability" }],
      value_streams: [{ id: "stage.buy", name: "Buy", archimate_type: "Value Stream" }],
      gates: [],
      pain_points: [],
      evidence_ids: ["evidence.onboarding"],
      confidence: { score: 0.91, rationale: "Verified onboarding relationships." }
    }
  }
};

const organizationProjection = {
  lens: "organization",
  context: {},
  archimate_legend: [{ type: "Business Actor", description: "An organizational entity." }],
  lanes: [],
  nodes: [
    {
      id: "person.john",
      name: "John",
      type: "person",
      archimate_type: "Business Actor",
      verification_state: "verified",
      review_state: "accepted",
      evidence_ids: ["evidence.seed_org"],
      confidence: null as never
    },
    {
      id: "person.maya",
      name: "Maya",
      type: "person",
      archimate_type: "Business Actor",
      verification_state: "verified",
      review_state: "accepted",
      evidence_ids: ["evidence.seed_org"],
      confidence: null as never
    }
  ],
  edges: [{ id: "rel.maya_reports_john", relationship: "reports_to", source_id: "person.maya", target_id: "person.john" }],
  process_contexts: {},
  overlays: [],
  unresolved: [],
  collapsible_branches: [{ entity_id: "person.john", state: "collapsible", summary: "John has 1 verified direct report and 0 unresolved associated relationships." }]
};

describe("MilkyWayMap", () => {
  afterEach(() => {
    cleanup();
  });

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
    expect(screen.getByText("Reads")).toBeInTheDocument();
    expect(screen.getByText("Lead Profile")).toBeInTheDocument();
    expect(screen.getByText("Creates")).toBeInTheDocument();
    expect(screen.getByText("Qualified Opportunity")).toBeInTheDocument();
    expect(screen.getByText("Updates")).toBeInTheDocument();
    expect(screen.getByText("Opportunity Record")).toBeInTheDocument();
    expect(screen.getByText("Deletes")).toBeInTheDocument();
    expect(screen.getByText("Stale Lead")).toBeInTheDocument();
    expect(screen.getByText("Should Priya be modeled as reporting to John?")).toBeInTheDocument();
  });

  it("replaces the default inspector relationships when a second process is selected", () => {
    render(<MilkyWayMap projection={projectionWithSecondProcess} />);

    expect(screen.getByText("Sales Lead")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Onboard Customer/ }));

    expect(screen.getByText("Onboarding Specialist")).toBeInTheDocument();
    expect(screen.getByText("Customer Portal")).toBeInTheDocument();
    expect(screen.queryByText("Sales Lead")).not.toBeInTheDocument();
    expect(screen.queryByText("CRM")).not.toBeInTheDocument();
  });

  it("renders organization payload nodes, relationships, and branches without lanes", () => {
    render(<MilkyWayMap projection={organizationProjection} />);

    expect(screen.getByText("John")).toBeInTheDocument();
    expect(screen.getByText("Maya")).toBeInTheDocument();
    expect(screen.getByText("Maya reports to John")).toBeInTheDocument();
    expect(screen.getByText(/John has 1 verified direct report/)).toBeInTheDocument();
    expect(screen.queryByText("0%")).not.toBeInTheDocument();
    expect(screen.getAllByText(/Confidence unavailable/).length).toBeGreaterThan(0);
  });

  it("renders relationship-aware unresolved process items in the inspector", () => {
    const unresolvedProcessProjection = {
      ...projection,
      process_contexts: {
        ...projection.process_contexts,
        "process.qualify_opportunity": {
          ...projection.process_contexts["process.qualify_opportunity"],
          unresolved: [{
            entity_id: "app.crm",
            relationship_id: "rel.qualify_crm_unresolved",
            relationship: "uses",
            question: "Is Qualify Opportunity supported by CRM?",
            evidence_ids: ["evidence.seed_process_web"],
            verification_state: "unresolved",
            review_state: "candidate",
            entity_verification_state: "verified",
            entity_review_state: "accepted"
          }]
        }
      }
    };

    render(<MilkyWayMap projection={unresolvedProcessProjection} />);

    expect(screen.getByText("What remains unresolved for this process?")).toBeInTheDocument();
    expect(screen.getByText("Is Qualify Opportunity supported by CRM?")).toBeInTheDocument();
  });
});

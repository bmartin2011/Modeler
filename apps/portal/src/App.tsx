import { ArtifactCards } from "./components/ArtifactCards";
import { FeedbackControls } from "./components/FeedbackControls";
import { MilkyWayMap } from "./components/MilkyWayMap";
import { QuestionPanel } from "./components/QuestionPanel";

const projection = {
  lens: "value_stream",
  sectors: [
    { id: "vs.discover", name: "Discover Opportunity", rings: ["purpose", "capability"] },
    { id: "vs.onboard", name: "Onboard Customer", rings: ["capability", "gate"] },
    { id: "vs.deliver", name: "Deliver Service", rings: ["system", "handoff"] }
  ],
  overlays: [{ type: "risk", label: "Approval gate concentration", confidence: 0.68 }],
  collapsible_branches: []
};

const answer = {
  question: "Who reports to John?",
  answer: "Maya and Luis are verified direct reports. Priya is unresolved.",
  known: ["Maya reports to John.", "Luis reports to John."],
  unknown: ["Priya is associated with John, but reporting is unresolved."],
  evidence_ids: ["evidence.seed_org", "evidence.user_luis"],
  confidence: { score: 0.86, rationale: "Two verified relationships." },
  next_best_question: "Should Priya be modeled as reporting to John?"
};

export default function App() {
  return (
    <main>
      <h1>Modeler</h1>
      <MilkyWayMap projection={projection} />
      <QuestionPanel answer={answer} />
      <FeedbackControls />
      <ArtifactCards />
    </main>
  );
}

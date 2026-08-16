import { useEffect, useState } from "react";
import { getMilkyWay } from "./api/client";
import { ArtifactCards } from "./components/ArtifactCards";
import { FeedbackControls } from "./components/FeedbackControls";
import { MilkyWayMap } from "./components/MilkyWayMap";
import { QuestionPanel } from "./components/QuestionPanel";

type Lens = "value_stream" | "organization";
type Projection = Awaited<ReturnType<typeof getMilkyWay>>;

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
  const [lens, setLens] = useState<Lens>("value_stream");
  const [projection, setProjection] = useState<Projection>();
  const [loadError, setLoadError] = useState(false);
  const [requestVersion, setRequestVersion] = useState(0);

  useEffect(() => {
    let active = true;

    setLoadError(false);
    setProjection(undefined);

    void getMilkyWay(lens)
      .then((nextProjection) => {
        if (active) {
          setProjection(nextProjection);
        }
      })
      .catch(() => {
        if (active) {
          setLoadError(true);
        }
      });

    return () => {
      active = false;
    };
  }, [lens, requestVersion]);

  return (
    <main>
      <h1>Modeler</h1>
      <nav aria-label="Milky Way lenses" className="lens-controls">
        <button type="button" aria-pressed={lens === "value_stream"} onClick={() => setLens("value_stream")}>
          Value Stream Lens
        </button>
        <button type="button" aria-pressed={lens === "organization"} onClick={() => setLens("organization")}>
          Organization Lens
        </button>
      </nav>
      {loadError ? (
        <section className="load-error" role="alert">
          <p>Unable to load the Milky Way.</p>
          <button type="button" onClick={() => setRequestVersion((version) => version + 1)}>
            Retry
          </button>
        </section>
      ) : projection ? (
        <MilkyWayMap projection={projection} />
      ) : (
        <p>Loading Milky Way...</p>
      )}
      <QuestionPanel answer={answer} />
      <FeedbackControls />
      <ArtifactCards />
    </main>
  );
}

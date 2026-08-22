import { useEffect, useState } from "react";
import {
  askQuestion,
  decideReviewQueueItem,
  getMilkyWay,
  getReviewQueue,
  previewReviewQueueItem,
  recordFeedback,
  ReviewQueueItem
} from "./api/client";
import { ArtifactCards } from "./components/ArtifactCards";
import { FeedbackControls } from "./components/FeedbackControls";
import { MilkyWayMap } from "./components/MilkyWayMap";
import { QuestionPanel } from "./components/QuestionPanel";

type Lens = "value_stream" | "organization";
type Projection = Awaited<ReturnType<typeof getMilkyWay>>;
type Answer = Awaited<ReturnType<typeof askQuestion>>;

function answerTargetId(question: string) {
  return `answer.${question.replace(/[^A-Za-z0-9]+/g, "_").replace(/^_|_$/g, "")}`;
}

const initialAnswer = {
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
  const [answer, setAnswer] = useState<Answer>(initialAnswer);
  const [reviewQueueItems, setReviewQueueItems] = useState<ReviewQueueItem[]>([]);
  const [loadError, setLoadError] = useState(false);
  const [requestVersion, setRequestVersion] = useState(0);
  const [reviewQueueVersion, setReviewQueueVersion] = useState(0);

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

  useEffect(() => {
    let active = true;

    void getReviewQueue()
      .then((queue) => {
        if (active) {
          setReviewQueueItems(queue.items);
        }
      })
      .catch(() => {
        if (active) {
          setReviewQueueItems([]);
        }
      });

    return () => {
      active = false;
    };
  }, [reviewQueueVersion]);

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
        <>
          {projection.context?.industry && projection.context?.journey ? (
            <section className="context-controls" aria-label="Model context">
              <label>
                Industry
                <select value={projection.context.industry.selected} disabled>
                  {projection.context.industry.available.map((industry: string) => <option key={industry}>{industry}</option>)}
                </select>
              </label>
              <label>
                Journey
                <select value={projection.context.journey.selected} disabled>
                  {projection.context.journey.available.map((journey: string) => <option key={journey}>{journey}</option>)}
                </select>
              </label>
            </section>
          ) : null}
          <MilkyWayMap projection={projection} showContext={false} />
        </>
      ) : (
        <p>Loading Milky Way...</p>
      )}
      <QuestionPanel
        answer={answer}
        onAskQuestion={async (question) => {
          setAnswer(await askQuestion(question));
        }}
      />
      <FeedbackControls
        targetId={answerTargetId(answer.question)}
        onRecordFeedback={async (payload) => {
          const event = await recordFeedback(payload);
          setReviewQueueVersion((version) => version + 1);
          return event;
        }}
      />
      <ArtifactCards
        reviewQueueItems={reviewQueueItems}
        onDecideReviewItem={async (feedbackId, reviewState) => {
          await decideReviewQueueItem(feedbackId, reviewState);
          setReviewQueueVersion((version) => version + 1);
        }}
        onPreviewReviewItem={previewReviewQueueItem}
      />
    </main>
  );
}

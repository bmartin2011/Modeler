import { useRef, useState } from "react";
import { PromotionPreview, ReviewQueueItem, ReviewState } from "../api/client";

type ReviewDecision = Exclude<ReviewState, "pending">;

export function ArtifactCards({
  reviewQueueItems,
  onDecideReviewItem,
  onPreviewReviewItem
}: {
  reviewQueueItems: ReviewQueueItem[];
  onDecideReviewItem: (feedbackId: string, reviewState: ReviewDecision) => Promise<void>;
  onPreviewReviewItem: (feedbackId: string) => Promise<PromotionPreview>;
}) {
  const [previews, setPreviews] = useState<Record<string, PromotionPreview>>({});
  const [actions, setActions] = useState<Record<string, { busy?: "preview" | "accepted" | "rejected"; error?: string }>>({});
  const inFlight = useRef<Set<string>>(new Set());
  const cards = [
    "Question Answer Card",
    "Textbook Pain Point Card",
    "Research Source Card",
    "RL and KPI Scorecard"
  ];

  async function previewItem(feedbackId: string) {
    if (inFlight.current.has(feedbackId)) {
      return;
    }

    inFlight.current.add(feedbackId);
    setActions((current) => ({ ...current, [feedbackId]: { busy: "preview" } }));
    try {
      const preview = await onPreviewReviewItem(feedbackId);
      setPreviews((current) => ({ ...current, [feedbackId]: preview }));
      setActions((current) => ({ ...current, [feedbackId]: {} }));
    } catch {
      setActions((current) => ({
        ...current,
        [feedbackId]: { error: "Unable to preview feedback." }
      }));
    } finally {
      inFlight.current.delete(feedbackId);
    }
  }

  async function decideItem(feedbackId: string, reviewState: ReviewDecision) {
    if (inFlight.current.has(feedbackId)) {
      return;
    }

    inFlight.current.add(feedbackId);
    setActions((current) => ({ ...current, [feedbackId]: { busy: reviewState } }));
    try {
      await onDecideReviewItem(feedbackId, reviewState);
      setActions((current) => ({ ...current, [feedbackId]: {} }));
    } catch {
      setActions((current) => ({
        ...current,
        [feedbackId]: { error: "Unable to record review decision." }
      }));
    } finally {
      inFlight.current.delete(feedbackId);
    }
  }

  return (
    <section className="artifact-grid">
      {cards.map((title) => (
        <article className="artifact-card" key={title}>
          <h3>{title}</h3>
          <p>Evidence, confidence, and feedback are visible by design.</p>
        </article>
      ))}
      <article className="artifact-card review-queue-card">
        <h3>Review Queue</h3>
        {reviewQueueItems.length ? (
          <ul className="review-queue-list">
            {reviewQueueItems.map((item) => {
              const action = actions[item.id];
              const busy = action?.busy;
              return (
                <li key={item.id}>
                  <strong>{item.rating.replace(/_/g, " ")}</strong>
                  <span>{item.target_id}</span>
                  <p>{item.comment}</p>
                  <div className="review-meta">
                    <small className={`review-state review-state-${item.review_state}`}>{item.review_state}</small>
                    {item.creates_learning_signal ? <small>Learning signal</small> : null}
                  </div>
                  {item.review_state === "pending" ? (
                    <div className="review-actions">
                      <button type="button" disabled={Boolean(busy)} onClick={() => void previewItem(item.id)}>
                        {busy === "preview" ? "Previewing..." : "Preview"}
                      </button>
                      <button type="button" disabled={Boolean(busy)} onClick={() => void decideItem(item.id, "accepted")}>
                        {busy === "accepted" ? "Accepting..." : "Accept"}
                      </button>
                      <button type="button" disabled={Boolean(busy)} onClick={() => void decideItem(item.id, "rejected")}>
                        {busy === "rejected" ? "Rejecting..." : "Reject"}
                      </button>
                    </div>
                  ) : null}
                  {action?.error ? (
                    <p className="review-action-error" role="alert">
                      {action.error}
                    </p>
                  ) : null}
                  {previews[item.id] ? (
                    <section className="promotion-preview" aria-label={`Promotion preview for ${item.id}`}>
                      <h4>Promotion Preview</h4>
                      <p>{previews[item.id].before.answer}</p>
                      <p>{previews[item.id].proposed.answer}</p>
                      {previews[item.id].added_known.length ? (
                        <div>
                          <strong>Known fact added</strong>
                          <ul>
                            {previews[item.id].added_known.map((fact) => (
                              <li key={fact}>Adds: {fact}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                      {previews[item.id].removed_unknown.length ? (
                        <div>
                          <strong>Unknown removed</strong>
                          <ul>
                            {previews[item.id].removed_unknown.map((unknown) => (
                              <li key={unknown}>Removes: {unknown}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </section>
                  ) : null}
                </li>
              );
            })}
          </ul>
        ) : (
          <p>No feedback waiting for review.</p>
        )}
      </article>
    </section>
  );
}

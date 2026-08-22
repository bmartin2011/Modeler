import { ThumbsDown, ThumbsUp } from "lucide-react";
import { FormEvent, useState } from "react";
import { FeedbackPayload } from "../api/client";

type FeedbackEvent = {
  creates_learning_signal: boolean;
};

export function FeedbackControls({
  targetId,
  onRecordFeedback
}: {
  targetId: string;
  onRecordFeedback: (payload: FeedbackPayload) => Promise<FeedbackEvent>;
}) {
  const [correctionOpen, setCorrectionOpen] = useState(false);
  const [correction, setCorrection] = useState("");
  const [recordedEvent, setRecordedEvent] = useState<FeedbackEvent>();
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState(false);

  async function submitFeedback(payload: FeedbackPayload) {
    if (isRecording) {
      return;
    }

    setIsRecording(true);
    setError(false);
    try {
      setRecordedEvent(await onRecordFeedback(payload));
      setCorrection("");
      setCorrectionOpen(false);
    } catch {
      setError(true);
    } finally {
      setIsRecording(false);
    }
  }

  async function handleCorrectionSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedCorrection = correction.trim();
    if (!trimmedCorrection) {
      return;
    }

    await submitFeedback({
      target_id: targetId,
      rating: "correction",
      comment: trimmedCorrection
    });
  }

  return (
    <div className="feedback-panel">
      <div className="feedback-controls" aria-label="feedback controls">
        <button
          type="button"
          aria-label="thumbs up"
          disabled={isRecording}
          onClick={() => submitFeedback({
            target_id: targetId,
            rating: "thumbs_up",
            comment: "Helpful answer."
          })}
        >
          <ThumbsUp size={18} />
        </button>
        <button
          type="button"
          aria-label="thumbs down"
          disabled={isRecording}
          onClick={() => {
            setCorrectionOpen(true);
            setRecordedEvent(undefined);
            setError(false);
          }}
        >
          <ThumbsDown size={18} />
        </button>
      </div>
      {correctionOpen ? (
        <form className="correction-form" onSubmit={handleCorrectionSubmit}>
          <label htmlFor="answer-correction">Correction</label>
          <textarea
            id="answer-correction"
            value={correction}
            onChange={(event) => setCorrection(event.target.value)}
          />
          <button type="submit" disabled={isRecording || !correction.trim()}>
            Record correction
          </button>
        </form>
      ) : null}
      {recordedEvent ? (
        <p className="feedback-status">
          Feedback recorded
          {recordedEvent.creates_learning_signal ? <span>Learning signal captured</span> : null}
        </p>
      ) : null}
      {error ? (
        <p className="feedback-error" role="alert">
          Unable to record feedback.
        </p>
      ) : null}
    </div>
  );
}

import { ThumbsDown, ThumbsUp } from "lucide-react";

export function FeedbackControls() {
  return (
    <div className="feedback-controls" aria-label="feedback controls">
      <button type="button" aria-label="thumbs up">
        <ThumbsUp size={18} />
      </button>
      <button type="button" aria-label="thumbs down">
        <ThumbsDown size={18} />
      </button>
    </div>
  );
}

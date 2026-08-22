export async function getMilkyWay(lens: "value_stream" | "organization") {
  const response = await fetch(`/api/views/milky-way?lens=${lens}`);

  if (!response.ok) {
    throw new Error(`Modeler API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export async function askQuestion(question: string) {
  const response = await fetch("/api/questions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question })
  });

  if (!response.ok) {
    throw new Error(`Modeler API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export type FeedbackRating = "thumbs_up" | "thumbs_down" | "correction" | "deviation";
export type ReviewState = "pending" | "accepted" | "rejected";

export type FeedbackPayload = {
  target_id: string;
  rating: FeedbackRating;
  comment: string;
};

export type ReviewQueueItem = FeedbackPayload & {
  id: string;
  creates_learning_signal: boolean;
  review_state: ReviewState;
};

export type LearningTrace = {
  feedback_id: string;
  target_id: string;
  comment: string;
  review_state: "accepted";
};

export type Answer = {
  question: string;
  answer: string;
  known: string[];
  unknown: string[];
  evidence_ids: string[];
  confidence: { score: number; rationale: string };
  next_best_question: string | null;
  learning_trace?: LearningTrace[];
};

export type PromotionPreview = {
  before: Answer;
  proposed: Answer;
  added_known: string[];
  removed_unknown: string[];
  learning_trace: LearningTrace[];
};

export async function recordFeedback(payload: FeedbackPayload) {
  const response = await fetch("/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Modeler API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

export async function getReviewQueue() {
  const response = await fetch("/api/review-queue");

  if (!response.ok) {
    throw new Error(`Modeler API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<{ items: ReviewQueueItem[] }>;
}

export async function decideReviewQueueItem(id: string, review_state: Exclude<ReviewState, "pending">) {
  const response = await fetch(`/api/review-queue/${id}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ review_state })
  });

  if (!response.ok) {
    throw new Error(`Modeler API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<ReviewQueueItem>;
}

export async function previewReviewQueueItem(id: string) {
  const response = await fetch(`/api/review-queue/${id}/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });

  if (!response.ok) {
    throw new Error(`Modeler API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<PromotionPreview>;
}

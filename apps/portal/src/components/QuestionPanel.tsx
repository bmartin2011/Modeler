import { FormEvent, useState } from "react";

type Answer = {
  question: string;
  answer: string;
  known: string[];
  unknown: string[];
  evidence_ids: string[];
  confidence: { score: number; rationale: string };
  next_best_question: string | null;
  learning_trace?: {
    feedback_id: string;
    target_id: string;
    comment: string;
    review_state: "accepted";
  }[];
};

export function QuestionPanel({
  answer,
  onAskQuestion
}: {
  answer: Answer;
  onAskQuestion: (question: string) => Promise<void>;
}) {
  const [question, setQuestion] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isAsking) {
      return;
    }

    setIsAsking(true);
    setError(false);
    try {
      await onAskQuestion(trimmedQuestion);
      setQuestion("");
    } catch {
      setError(true);
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <section className="question-panel">
      <form className="question-form" onSubmit={handleSubmit}>
        <label htmlFor="model-question">Ask a model question</label>
        <div className="question-input-row">
          <input
            id="model-question"
            type="text"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <button type="submit" disabled={isAsking || !question.trim()}>
            {isAsking ? "Asking..." : "Ask"}
          </button>
        </div>
      </form>
      {error ? (
        <p className="question-error" role="alert">
          Unable to answer that question.
        </p>
      ) : null}
      <h2>Question</h2>
      <p>{answer.question}</p>
      <h3>Answer</h3>
      <p>{answer.answer}</p>
      <strong>{Math.round(answer.confidence.score * 100)}% confidence</strong>
      {answer.learning_trace?.length ? (
        <section className="learning-trace" aria-label="Learning trace">
          <h3>Learned from accepted feedback</h3>
          <ul>
            {answer.learning_trace.map((trace) => (
              <li key={trace.feedback_id}>
                <strong>{trace.feedback_id}</strong>
                <span>{trace.comment}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <h3>Evidence</h3>
      <ul>
        {answer.evidence_ids.map((id) => (
          <li key={id}>{id}</li>
        ))}
      </ul>
      {answer.next_best_question && (
        <>
          <h3>Next Best Question</h3>
          <p>{answer.next_best_question}</p>
        </>
      )}
    </section>
  );
}

type Answer = {
  question: string;
  answer: string;
  known: string[];
  unknown: string[];
  evidence_ids: string[];
  confidence: { score: number; rationale: string };
  next_best_question: string | null;
};

export function QuestionPanel({ answer }: { answer: Answer }) {
  return (
    <section className="question-panel">
      <h2>Question</h2>
      <p>{answer.question}</p>
      <h3>Answer</h3>
      <p>{answer.answer}</p>
      <strong>{Math.round(answer.confidence.score * 100)}% confidence</strong>
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

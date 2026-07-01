export type TopicScore = {
  topic_title: string;
  topic_score: number;
  feedback: string;
};

export type Scorecard = {
  topic_scores: TopicScore[];
  overall_assessment: string;
  strengths: string[];
  gaps: string[];
  focus_recommendation: string;
};

interface ScorecardViewProps {
  scorecard: Scorecard;
}

export function ScorecardView({ scorecard }: ScorecardViewProps) {
  return (
    <div className="w-full space-y-4">
      <div className="card px-4 py-4">
        <div className="text-[13px] font-semibold text-ink">
          Overall assessment
        </div>
        <p className="mt-1.5 text-[13px] leading-relaxed text-body">
          {scorecard.overall_assessment}
        </p>
      </div>

      <div className="card px-4 py-4">
        <div className="text-[13px] font-semibold text-ink">Topic scores</div>
        <div className="mt-3 space-y-3">
          {scorecard.topic_scores.map((t, i) => (
            <div
              key={i}
              className="border-b border-line pb-3 last:border-b-0 last:pb-0"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-[13px] font-medium text-ink">
                  {t.topic_title}
                </span>
                <span
                  className="flex gap-0.5 text-sm"
                  aria-label={`${t.topic_score} out of 5`}
                >
                  {Array.from({ length: 5 }, (_, j) => (
                    <span
                      key={j}
                      className={
                        j < t.topic_score ? "text-primary" : "text-line-strong"
                      }
                    >
                      ●
                    </span>
                  ))}
                </span>
              </div>
              <p className="mt-1 text-[12.5px] leading-relaxed text-muted">
                {t.feedback}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="card px-4 py-4">
          <div className="text-[13px] font-semibold text-success">
            Strengths
          </div>
          <ul className="mt-2 space-y-1.5">
            {scorecard.strengths.map((s, i) => (
              <li
                key={i}
                className="flex gap-1.5 text-[12.5px] leading-relaxed text-body"
              >
                <span className="text-success">+</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
        <div className="card px-4 py-4">
          <div className="text-[13px] font-semibold text-warning">
            Areas to grow
          </div>
          <ul className="mt-2 space-y-1.5">
            {scorecard.gaps.map((g, i) => (
              <li
                key={i}
                className="flex gap-1.5 text-[12.5px] leading-relaxed text-body"
              >
                <span className="text-warning">–</span>
                {g}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card bg-primary-wash px-4 py-4">
        <div className="text-[13px] font-semibold text-primary-ink">
          What to focus on next
        </div>
        <p className="mt-1.5 text-[13px] leading-relaxed text-primary-ink">
          {scorecard.focus_recommendation}
        </p>
      </div>
    </div>
  );
}

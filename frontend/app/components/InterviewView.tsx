"use client";
import { useEffect, useRef } from "react";

import { Header } from "./Header";
import { ScorecardView, type Scorecard } from "./ScorecardView";

export type Turn = {
  role: "interviewer" | "candidate";
  text: string;
};

/** Soft target used only for the progress bar; the real cap lives server-side. */
const PROGRESS_TARGET = 12;

interface InterviewViewProps {
  transcript: Turn[];
  questionCount: number;
  done: boolean;
  answer: string;
  onAnswerChange: (value: string) => void;
  onSubmit: () => void;
  isReplying: boolean;
  replyError: string;
  onRestart: () => void;
  onEndInterview: () => void;
  scorecard: Scorecard | null;
  isFinishing: boolean;
  finishError: string;
}

export function InterviewView({
  transcript,
  questionCount,
  done,
  answer,
  onAnswerChange,
  onSubmit,
  isReplying,
  replyError,
  onRestart,
  onEndInterview,
  scorecard,
  isFinishing,
  finishError,
}: InterviewViewProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Keep the newest message in view as the conversation grows.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript.length, done, isReplying]);

  const progress = Math.min(100, (questionCount / PROGRESS_TARGET) * 100);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  }

  return (
    <div className="flex h-dvh w-full flex-col font-sans">
      {/* App bar + progress */}
      <div className="shrink-0 bg-surface">
        <Header
          right={
            <button
              onClick={onRestart}
              className="rounded-md border border-line-strong px-2.5 py-1 text-xs text-muted transition-colors hover:text-ink"
            >
              {done ? "New interview" : "Start over"}
            </button>
          }
        />
        <div className="border-b border-line px-4 py-3 sm:px-6">
          <div className="w-full">
            <div className="mb-2 flex items-center justify-between text-[11.5px]">
              <span className="font-semibold text-ink">
                {done ? "Interview complete" : "In progress"}
              </span>
              <div className="flex items-center gap-3">
                <span className="text-faint">Question {questionCount}</span>
                {!done && (
                  <button
                    onClick={onEndInterview}
                    disabled={isFinishing}
                    className="text-primary transition-opacity hover:underline disabled:opacity-50"
                  >
                    End interview
                  </button>
                )}
              </div>
            </div>
            <div className="h-1 w-full overflow-hidden rounded-full bg-line">
              <span
                className="block h-full rounded-full bg-primary transition-all duration-500"
                style={{ width: `${done ? 100 : progress}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Transcript — fills the viewport, readable column centered */}
      <div className="flex-1 overflow-y-auto bg-canvas">
        <div className="w-full space-y-3.5 px-4 py-6 sm:px-6">
          {transcript.map((turn, i) =>
            turn.role === "interviewer" ? (
              <div
                key={i}
                className="max-w-[84%] whitespace-pre-wrap break-words rounded-[13px_13px_13px_4px] bg-bubble px-3.5 py-2.5 text-[13px] leading-relaxed text-ink"
              >
                {turn.text}
              </div>
            ) : (
              <div
                key={i}
                className="ml-auto max-w-[84%] whitespace-pre-wrap break-words rounded-[13px_13px_4px_13px] bg-primary-tint px-3.5 py-2.5 text-[13px] leading-relaxed text-primary-ink"
              >
                {turn.text}
              </div>
            ),
          )}

          {isReplying && (
            <div className="max-w-[84%] rounded-[13px_13px_13px_4px] bg-bubble px-3.5 py-2.5 text-[13px] text-faint">
              <span className="animate-pulse">Interviewer is thinking…</span>
            </div>
          )}

          {done && scorecard && <ScorecardView scorecard={scorecard} />}

          {done && !scorecard && (
            <div className="rounded-xl border border-line bg-surface px-4 py-3.5 text-center text-[13px] leading-relaxed text-body">
              {finishError ? (
                <span className="text-warning">{finishError}</span>
              ) : (
                <span className="animate-pulse text-faint">
                  Generating your feedback report…
                </span>
              )}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Composer / finished footer — pinned to the bottom edge */}
      <div className="shrink-0 border-t border-line bg-surface">
        <div className="w-full px-4 py-3.5 sm:px-6">
          {done ? (
            <button
              onClick={onRestart}
              className="w-full rounded-[10px] bg-primary py-3 text-sm font-semibold text-white shadow-lg shadow-primary/30 transition-opacity hover:opacity-95"
            >
              Start a new interview
            </button>
          ) : (
            <>
              <div className="flex items-end gap-2.5">
                <textarea
                  rows={1}
                  placeholder="Type your answer…"
                  value={answer}
                  onChange={(e) => onAnswerChange(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isReplying}
                  className="max-h-40 min-w-0 flex-1 resize-none break-words rounded-[9px] border border-line-strong bg-surface px-3.5 py-2.5 text-[13px] leading-relaxed text-body outline-none placeholder:text-faint focus:border-primary disabled:opacity-60"
                />
                <button
                  onClick={onSubmit}
                  disabled={isReplying || !answer.trim()}
                  aria-label="Send answer"
                  className="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-[9px] bg-primary text-lg text-white transition-opacity hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  {isReplying ? "…" : "↑"}
                </button>
              </div>
              {replyError && (
                <p className="mt-2 text-[11.5px] text-warning">{replyError}</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

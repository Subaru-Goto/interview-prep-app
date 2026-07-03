"use client";
import { useState } from "react";

import { InterviewView } from "./components/InterviewView";
import { SetupView } from "./components/SetupView";
import { useCvUpload } from "./hooks/useCvUpload";
import { useInterview } from "./hooks/useInterview";

// UX hints only — backend's validators are the source of truth.
const MIN_JD = 200;
const MAX_JD = 20000;

export default function Home() {
  const [jobDescription, setJobDescription] = useState("");
  const { status, isUsable, cvText, uploadCv } = useCvUpload();
  const {
    sessionId,
    transcript,
    answer,
    setAnswer,
    isStarting,
    startError,
    isReplying,
    replyError,
    done,
    scorecard,
    isFinishing,
    finishError,
    sessionCost,
    startInterview,
    submitReply,
    restart,
    handleEndInterview,
  } = useInterview();

  const jdLen = jobDescription.trim().length;
  const canStart = isUsable && jdLen >= MIN_JD && jdLen <= MAX_JD;
  const startHint = !isUsable
    ? "Upload a CV to begin."
    : jdLen < MIN_JD
      ? `Job description needs at least ${MIN_JD} characters (currently ${jdLen}).`
      : "";

  const questionCount = transcript.filter(
    (t) => t.role === "interviewer",
  ).length;

  return (
    <main className="h-dvh">
      {sessionId ? (
        <InterviewView
          transcript={transcript}
          questionCount={questionCount}
          done={done}
          answer={answer}
          onAnswerChange={setAnswer}
          onSubmit={submitReply}
          isReplying={isReplying}
          replyError={replyError}
          onRestart={restart}
          onEndInterview={handleEndInterview}
          scorecard={scorecard}
          isFinishing={isFinishing}
          finishError={finishError}
          sessionCost={sessionCost}
        />
      ) : (
        <SetupView
          status={status}
          isUsable={isUsable}
          onUpload={uploadCv}
          jobDescription={jobDescription}
          onJobDescriptionChange={setJobDescription}
          maxJd={MAX_JD}
          canStart={canStart}
          isStarting={isStarting}
          startHint={startHint}
          startError={startError}
          onStart={() => startInterview(cvText, jobDescription)}
        />
      )}
    </main>
  );
}

"use client";
import { useState } from "react";

import { InterviewView, type Turn } from "./components/InterviewView";
import type { Scorecard } from "./components/ScorecardView";
import type { SessionCost } from "./components/SessionCostFooter";
import { SetupView } from "./components/SetupView";

// UX hints only — backend's validators are the source of truth.
const MIN_JD = 200;
const MAX_JD = 20000;

export default function Home() {
  // setup
  const [status, setStatus] = useState("");
  const [isUsable, setIsUsable] = useState(false);
  const [cvText, setCVText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState("");

  // interview
  const [sessionId, setSessionId] = useState("");
  const [transcript, setTranscript] = useState<Turn[]>([]);
  const [answer, setAnswer] = useState("");
  const [isReplying, setIsReplying] = useState(false);
  const [replyError, setReplyError] = useState("");
  const [done, setDone] = useState(false);
  const [scorecard, setScorecard] = useState<Scorecard | null>(null);
  const [isFinishing, setIsFinishing] = useState(false);
  const [finishError, setFinishError] = useState("");
  const [sessionCost, setSessionCost] = useState<SessionCost | null>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

  async function uploadCv(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE_URL}/upload-cv`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      setStatus("✗ " + err.detail);
      return;
    }
    const data = await res.json();
    setStatus(
      data.is_usable
        ? "✓ CV uploaded successfully"
        : "✗ Couldn't read text from this PDF — please upload a text-based PDF.",
    );
    setIsUsable(data.is_usable);
    setCVText(data.text ?? "");
  }

  async function startInterview() {
    setIsStarting(true);
    setStartError("");
    try {
      const res = await fetch(`${API_BASE_URL}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cv_text: cvText, jd_text: jobDescription }),
      });
      if (!res.ok) {
        const err = await res.json();
        setStartError("✗ " + (err.detail ?? "Could not start the interview."));
        return;
      }
      const data = await res.json();
      setSessionId(data.session_id);
      setTranscript([{ role: "interviewer", text: data.first_question }]);
      setSessionCost(data.session_cost);
    } catch (error) {
      console.error("Error starting interview:", error);
      setStartError("✗ An error occurred while starting the interview.");
    } finally {
      setIsStarting(false);
    }
  }

  async function submitReply() {
    const text = answer.trim();
    if (!text || isReplying || done) return;

    setIsReplying(true);
    setReplyError("");
    // show the candidate's answer immediately
    setTranscript((prev) => [...prev, { role: "candidate", text }]);
    setAnswer("");

    try {
      const res = await fetch(`${API_BASE_URL}/reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, answer: text }),
      });
      if (!res.ok) {
        const err = await res.json();
        setReplyError("✗ " + (err.detail ?? "Something went wrong."));
        return;
      }
      const data = await res.json();
      setSessionCost(data.session_cost);
      if (data.done) {
        setDone(true);
        await finishInterview();
      } else {
        setTranscript((prev) => [
          ...prev,
          { role: "interviewer", text: data.next_question },
        ]);
      }
    } catch (error) {
      console.error("Error sending reply:", error);
      setReplyError("✗ A network error occurred — please try again.");
    } finally {
      setIsReplying(false);
    }
  }

  async function finishInterview() {
    setIsFinishing(true);
    setFinishError("");
    try {
      const res = await fetch(`${API_BASE_URL}/finish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
      if (!res.ok) {
        const err = await res.json();
        setFinishError(
          "✗ " + (err.detail ?? "Could not generate your feedback report."),
        );
        return;
      }
      const data = await res.json();
      setScorecard(data.scorecard);
      setSessionCost(data.session_cost);
    } catch (error) {
      console.error("Error finishing interview:", error);
      setFinishError("✗ A network error occurred — please try again.");
    } finally {
      setIsFinishing(false);
    }
  }

  async function handleEndInterview() {
    if (!sessionId || done || isFinishing) return;

    const hasAnswered = transcript.some((t) => t.role === "candidate");
    if (!hasAnswered) {
      if (
        !window.confirm(
          "You haven't answered any questions yet, so there's no feedback to generate. End the interview and return to the setup page?",
        )
      ) {
        return;
      }
      restart();
      return;
    }

    if (!window.confirm("End the interview now and see your feedback report?")) {
      return;
    }
    setDone(true);
    await finishInterview();
  }

  function restart() {
    // keep cv/jd so a fresh run with the same inputs is one click away
    setSessionId("");
    setTranscript([]);
    setAnswer("");
    setDone(false);
    setReplyError("");
    setStartError("");
    setScorecard(null);
    setIsFinishing(false);
    setFinishError("");
    setSessionCost(null);
  }

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
          onStart={startInterview}
        />
      )}
    </main>
  );
}

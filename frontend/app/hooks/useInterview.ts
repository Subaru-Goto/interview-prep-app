"use client";
import { useState } from "react";

import type { Turn } from "../components/InterviewView";
import type { Scorecard } from "../components/ScorecardView";
import type { SessionCost } from "../components/SessionCostFooter";
import { apiCall, apiErrorMessage } from "../lib/api";

interface StartResponse {
  session_id: string;
  first_question: string;
  session_cost: SessionCost;
}

interface ReplyResponse {
  done: boolean;
  next_question: string | null;
  session_cost: SessionCost;
}

interface FinishResponse {
  scorecard: Scorecard;
  session_cost: SessionCost;
}

export function useInterview() {
  const [sessionId, setSessionId] = useState("");
  const [transcript, setTranscript] = useState<Turn[]>([]);
  const [answer, setAnswer] = useState("");
  const [isStarting, setIsStarting] = useState(false);
  const [startError, setStartError] = useState("");
  const [isReplying, setIsReplying] = useState(false);
  const [replyError, setReplyError] = useState("");
  const [done, setDone] = useState(false);
  const [scorecard, setScorecard] = useState<Scorecard | null>(null);
  const [isFinishing, setIsFinishing] = useState(false);
  const [finishError, setFinishError] = useState("");
  const [sessionCost, setSessionCost] = useState<SessionCost | null>(null);

  async function startInterview(cvText: string, jobDescription: string) {
    setIsStarting(true);
    setStartError("");
    try {
      const data = await apiCall<StartResponse>("/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cv_text: cvText, jd_text: jobDescription }),
      });
      setSessionId(data.session_id);
      setTranscript([{ role: "interviewer", text: data.first_question }]);
      setSessionCost(data.session_cost);
    } catch (error) {
      setStartError(
        apiErrorMessage(error, "An error occurred while starting the interview."),
      );
    } finally {
      setIsStarting(false);
    }
  }

  async function finishInterview() {
    setIsFinishing(true);
    setFinishError("");
    try {
      const data = await apiCall<FinishResponse>("/finish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      });
      setScorecard(data.scorecard);
      setSessionCost(data.session_cost);
    } catch (error) {
      setFinishError(
        apiErrorMessage(error, "A network error occurred — please try again."),
      );
    } finally {
      setIsFinishing(false);
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
      const data = await apiCall<ReplyResponse>("/reply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, answer: text }),
      });
      setSessionCost(data.session_cost);
      if (data.done) {
        setDone(true);
        await finishInterview();
      } else {
        setTranscript((prev) => [
          ...prev,
          { role: "interviewer", text: data.next_question ?? "" },
        ]);
      }
    } catch (error) {
      setReplyError(
        apiErrorMessage(error, "A network error occurred — please try again."),
      );
    } finally {
      setIsReplying(false);
    }
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

  return {
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
  };
}

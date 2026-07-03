"use client";
import { useRef, useState } from "react";

import type { Turn } from "../components/InterviewView";
import type { Scorecard } from "../components/ScorecardView";
import type { SessionCost } from "../components/SessionCostFooter";
import { API_BASE_URL, apiCall, apiErrorMessage } from "../lib/api";

interface StartResponse {
  session_id: string;
  session_cost: SessionCost;
}

interface ReplyResponse {
  done: boolean;
  session_cost: SessionCost;
}

interface FinishResponse {
  scorecard: Scorecard;
  session_cost: SessionCost;
}

type QuestionStreamEvent =
  | { type: "token"; text: string }
  | { type: "done"; session_cost: SessionCost }
  | { type: "error"; message: string };

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
  const questionStream = useRef<EventSource | null>(null);

  /** Stream a question (opening or follow-up) from `url`, appending it to
   * the transcript token by token as it arrives. Shared by startInterview
   * and submitReply — the only difference between the two is the endpoint
   * and where errors should surface. */
  function streamQuestion(url: string, onError: (message: string) => void) {
    setIsReplying(true); // "nothing to show yet" — same signal for both cases
    let receivedFirstToken = false;

    const source = new EventSource(url);
    questionStream.current = source;

    source.onmessage = (event) => {
      const payload: QuestionStreamEvent = JSON.parse(event.data);

      if (payload.type === "token") {
        if (!receivedFirstToken) {
          receivedFirstToken = true;
          setIsReplying(false);
          setTranscript((prev) => [
            ...prev,
            { role: "interviewer", text: payload.text },
          ]);
        } else {
          setTranscript((prev) => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            updated[updated.length - 1] = { ...last, text: last.text + payload.text };
            return updated;
          });
        }
        return;
      }

      source.close();
      questionStream.current = null;
      if (payload.type === "done") {
        setSessionCost(payload.session_cost);
      } else {
        setIsReplying(false);
        onError(payload.message);
      }
    };

    source.onerror = () => {
      source.close();
      questionStream.current = null;
      setIsReplying(false);
      onError("A network error occurred while loading the next question.");
    };
  }

  async function startInterview(cvText: string, jobDescription: string) {
    setIsStarting(true);
    setStartError("");
    try {
      const data = await apiCall<StartResponse>("/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cv_text: cvText, jd_text: jobDescription }),
      });
      // Navigate to the interview screen immediately — don't wait for the
      // opening question, which streams in separately once we're there.
      setSessionId(data.session_id);
      setSessionCost(data.session_cost);
      streamQuestion(`${API_BASE_URL}/start/${data.session_id}/stream`, (message) =>
        setStartError("✗ " + message),
      );
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
        setIsReplying(false);
        setDone(true);
        await finishInterview();
      } else {
        streamQuestion(`${API_BASE_URL}/reply/${sessionId}/stream`, (message) =>
          setReplyError("✗ " + message),
        );
      }
    } catch (error) {
      setIsReplying(false);
      setReplyError(
        apiErrorMessage(error, "A network error occurred — please try again."),
      );
    }
  }

  function restart() {
    // stop a still-streaming question from writing into the reset state
    questionStream.current?.close();
    questionStream.current = null;

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

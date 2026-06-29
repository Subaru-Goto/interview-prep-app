"use client";
import {useState} from "react";

export default function Home() {
  const [message, setMessage] = useState("");
  const [content, setContent] = useState("");
  const [status, setStatus] = useState("");
  const [isUsable, setIsUsable] = useState(false);
  const [cvText, setCVText] = useState("");
  const [jobDescription, setJobDescription] = useState("");

  const [sessionId, setSessionId] = useState("");
  const [firstQuestion, setFirstQuestion] = useState("");
  const [startError, setStartError] = useState("");
  const [isStarting, setIsStarting] = useState(false);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

  async function sendMessage() {
    if (!message.trim()) return;

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await res.json();
      setContent(data.content);
    } catch (error) {
      console.error("Error fetching chat replay:", error);
      setContent("An error occurred while fetching the chat replay");
    }
  }

  async function uploadCv(file: File) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE_URL}/upload-cv`,
       { method: "POST", body: formData }
      );

    if (!res.ok) {
      const err = await res.json();
      setStatus("✗ " + err.detail);
      return;
    }
    const data = await res.json();
    setStatus(data.is_usable
    ? "✓ CV uploaded successfully"
    : "✗ Couldn't read text from this PDF — please upload a text-based PDF.");

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
      setFirstQuestion(data.first_question);
    } catch (error) {
      console.error("Error starting interview:", error);
      setStartError("✗ An error occurred while starting the interview.");
    } finally {
      setIsStarting(false);
    }
  }

  // UX hints only — backend's validate_inputs is the source of truth.
  const MIN_JD = 200;
  const MAX_JD = 20000;

  const jdLen = jobDescription.trim().length;
  const canStart = isUsable && jdLen >= MIN_JD && jdLen <= MAX_JD;

  const startHint = !isUsable
    ? "Upload a CV to begin."
    : jdLen < MIN_JD
    ? `Job description needs at least ${MIN_JD} characters (currently ${jdLen}).`
    : "";

  if (sessionId) {
    return (
      <main>
        <h2>Interview</h2>
        <p>{firstQuestion}</p>
      </main>
    );
  }

  return (
    <>
      <input
        placeholder="insert test text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />
      <button onClick={sendMessage}>Send</button>
      {content && <p>{content}</p>}

      <input type="file" accept="application/pdf"
       onChange={(e) => e.target.files?.[0] && uploadCv(e.target.files[0])} />
      {status && <p>{status}</p>}

      <textarea
        placeholder="copy and paste job description"
        value={jobDescription}
        maxLength={MAX_JD}
        onChange={ (e) => setJobDescription(e.target.value)}
      />
      <p>{jobDescription.length} / {MAX_JD}</p>

      {startHint && <p>{startHint}</p>}
      <button disabled={!canStart || isStarting} onClick={startInterview}>
        {isStarting ? "Starting…" : "Start interview"}
      </button>
      {startError && <p>{startError}</p>}
    </>
  );
}

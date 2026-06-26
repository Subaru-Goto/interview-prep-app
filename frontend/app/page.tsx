"use client";
import {useState} from "react";

export default function Home() {
  const [message, setMessage] = useState("");
  const [content, setContent] = useState("");
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
  return (
    <>
      <input 
        placeholder="insert test text"
        value={message} 
        onChange={(e) => setMessage(e.target.value)} 
      />
      <button onClick={sendMessage}>Send</button>
      {content && <p>{content}</p>}
    </>
  );
}

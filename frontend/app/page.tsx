"use client";
import {useState} from "react";

export default function Home() {
  const [message, setMessage] = useState("");
  const [replay, setReply] = useState("");
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
      setReply(data.reply);
    } catch (error) {
      console.error("Error fetching chat replay:", error);
      setReply("An error occurred while fetching the chat replay");
    }
  }
  return (
    <></>
  );
}

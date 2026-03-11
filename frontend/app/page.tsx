"use client";

import { useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("");
  const [reply, setReply] = useState("");

  const sendMessage = async () => {
    const res = await fetch("http://127.0.0.1:8001/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    const data = await res.json();
    setReply(data.reply);
  };

  return (
    <div style={{ padding: 40 }}>
      <h1>Putty Chat</h1>

      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="輸入訊息"
      />

      <button onClick={sendMessage}>送出</button>

      <p>AI：{reply}</p>
    </div>
  );
}
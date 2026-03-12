// /frontend/app/page.tsx

"use client";

import { useEffect, useRef, useState } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export default function Home() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!message.trim() || loading) return;

    if (!API_BASE_URL) {
      console.error("NEXT_PUBLIC_API_BASE_URL 未設定");
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "前端環境變數 NEXT_PUBLIC_API_BASE_URL 未設定。" },
      ]);
      return;
    }

    const userMessage: Message = {
      role: "user",
      content: message,
    };

    const updatedMessages = [...messages, userMessage];
    const recentMessages = updatedMessages.slice(-10);

    setMessages([...updatedMessages, { role: "assistant", content: "" }]);
    setMessage("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/chat-stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: recentMessages,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      if (!res.body) {
        throw new Error("沒有收到串流資料");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let text = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        text += chunk;

        setMessages([
          ...updatedMessages,
          { role: "assistant", content: text },
        ]);
      }
    } catch (error) {
      console.error(error);
      setMessages([
        ...updatedMessages,
        { role: "assistant", content: "發生錯誤，請確認後端是否正常。" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !loading) {
      sendMessage();
    }
  };

  return (
    <main
      style={{
        padding: 40,
        maxWidth: 900,
        margin: "0 auto",
        minHeight: "100vh",
      }}
    >
      <h1 style={{ fontSize: 32, fontWeight: "bold", marginBottom: 20 }}>
        Putty Chat
      </h1>

      <div
        style={{
          border: "1px solid #ccc",
          borderRadius: 12,
          padding: 16,
          height: 500,
          overflowY: "auto",
          marginBottom: 20,
        }}
      >
        {messages.length === 0 ? (
          <p>開始聊天吧！</p>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              style={{
                marginBottom: 16,
                textAlign: msg.role === "user" ? "right" : "left",
              }}
            >
              <div
                style={{
                  display: "inline-block",
                  padding: "10px 14px",
                  borderRadius: 12,
                  backgroundColor:
                    msg.role === "user" ? "#2563eb" : "#e5e7eb",
                  color: msg.role === "user" ? "white" : "black",
                  maxWidth: "70%",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  lineHeight: 1.6,
                }}
              >
                <strong>{msg.role === "user" ? "你" : "AI"}：</strong>
                {msg.content || (loading && msg.role === "assistant" ? "思考中..." : "")}
              </div>
            </div>
          ))
        )}

        <div ref={bottomRef} />
      </div>

      <div style={{ display: "flex", gap: 12 }}>
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={loading ? "AI 生成中..." : "輸入訊息"}
          disabled={loading}
          style={{
            flex: 1,
            padding: 12,
            border: "1px solid #ccc",
            borderRadius: 8,
            opacity: loading ? 0.6 : 1,
            fontSize: 16,
          }}
        />

        <button
          onClick={sendMessage}
          disabled={loading}
          style={{
            padding: "12px 20px",
            borderRadius: 8,
            border: "none",
            backgroundColor: "#111827",
            color: "white",
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.7 : 1,
            fontSize: 16,
          }}
        >
          {loading ? "生成中..." : "送出"}
        </button>
      </div>
    </main>
  );
}
"use client";

import { useState, useRef, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { auth } from "@/lib/auth";
import { apiChat } from "@/lib/api";
import { ChatMessage } from "@/types";

export default function ChatPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!auth.isLoggedIn()) { router.push("/login"); return; }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const data = await apiChat.send(id, input) as any;
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: data.answer || data.response || data.message || JSON.stringify(data),
        sources: data.sources || [],
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: "Error: " + err.message,
      }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      {/* Navbar */}
      <div className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-white text-sm transition-colors">
            ← Dashboard
          </button>
          <span className="text-gray-600">|</span>
          <nav className="flex gap-4 text-sm">
            <button onClick={() => router.push(`/workspaces/${id}/files`)} className="text-gray-400 hover:text-white transition-colors">Files</button>
            <span className="text-white font-medium">Chat</span>
            <button onClick={() => router.push(`/workspaces/${id}/graph`)} className="text-gray-400 hover:text-white transition-colors">Graph</button>
            <button onClick={() => router.push(`/workspaces/${id}/research`)} className="text-gray-400 hover:text-white transition-colors">Research</button>
          </nav>
        </div>
        <button onClick={() => { auth.logout(); router.push("/login"); }} className="text-gray-400 hover:text-white text-sm transition-colors">
          Sign out
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 max-w-4xl w-full mx-auto space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            Ask anything about your uploaded documents.
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-2xl rounded-2xl px-5 py-4 ${
              msg.role === "user"
                ? "bg-blue-600 text-white"
                : "bg-gray-900 border border-gray-800 text-gray-100"
            }`}>
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700 space-y-1">
                  <p className="text-xs text-gray-400 font-medium">Sources</p>
                  {msg.sources.map((src, j) => (
                    <div key={j} className="text-xs text-gray-400 bg-gray-800 rounded px-3 py-2">
                      <span className="text-blue-400">{src.filename}</span>
                      <span className="text-gray-500 ml-2">score: {src.score?.toFixed(2)}</span>
                      <p className="text-gray-500 mt-1 line-clamp-2">{src.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-900 border border-gray-800 rounded-2xl px-5 py-4">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 p-4">
        <form onSubmit={handleSend} className="max-w-4xl mx-auto flex gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your documents..."
            className="flex-1 bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 text-white px-6 py-3 rounded-xl transition-colors font-medium"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
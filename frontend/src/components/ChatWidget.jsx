import { useState, useRef, useEffect } from "react";
import { chatService } from "../services";
import { useAuth } from "../context/AuthContext";

const SUGGESTED = [
  "Gợi ý sách hay cho tôi",
  "Sách nào đang hot nhất?",
  "Cách thêm vào giỏ hàng?",
  "Sách giá rẻ dưới 100k",
];

export default function ChatWidget() {
  const { customer } = useAuth();
  const [open, setOpen]       = useState(false);
  const [input, setInput]     = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Xin chào! Tôi là trợ lý BookStore AI. Hỏi tôi về sách, gợi ý mua hàng hoặc bất kỳ điều gì bạn cần!",
      time: new Date(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const userId = customer?.id?.toString() || "";

  const send = async (text) => {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput("");

    const userMsg = { role: "user", content: msg, time: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const history = messages.slice(-6).map(({ role, content }) => ({ role, content }));
      const res     = await chatService.send(msg, userId, history);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.data.reply, time: new Date() },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Xin lỗi, có lỗi xảy ra. Vui lòng thử lại!", time: new Date() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fmt = (d) =>
    d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-2xl
                   bg-gradient-to-br from-primary-600 to-primary-800
                   flex items-center justify-center text-white text-2xl
                   hover:scale-110 transition-transform"
        aria-label="Mở chat tư vấn"
      >
        {open ? "✕" : "💬"}
      </button>

      {/* Chat panel */}
      {open && (
        <div
          className="fixed bottom-24 right-6 z-50 w-[360px] max-h-[560px]
                     flex flex-col rounded-2xl shadow-2xl overflow-hidden
                     border border-gray-200 bg-white"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-primary-600 to-primary-800 px-4 py-3 flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-lg">
              🤖
            </div>
            <div className="flex-1">
              <p className="text-white font-semibold text-sm">BookStore AI</p>
              <p className="text-primary-200 text-xs">Trợ lý tư vấn sách thông minh</p>
            </div>
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 bg-gray-50 min-h-0"
               style={{ maxHeight: "340px" }}>
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                {m.role === "assistant" && (
                  <div className="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center text-sm mr-2 flex-shrink-0 mt-1">
                    🤖
                  </div>
                )}
                <div className={`max-w-[78%] ${m.role === "user" ? "items-end" : "items-start"} flex flex-col`}>
                  <div
                    className={`px-3 py-2 rounded-2xl text-sm leading-relaxed
                      ${m.role === "user"
                        ? "bg-primary-600 text-white rounded-br-sm"
                        : "bg-white text-gray-800 shadow-sm border border-gray-100 rounded-bl-sm"
                      }`}
                  >
                    {m.content}
                  </div>
                  <span className="text-[10px] text-gray-400 mt-1 px-1">{fmt(m.time)}</span>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="w-7 h-7 rounded-full bg-primary-100 flex items-center justify-center text-sm mr-2">
                  🤖
                </div>
                <div className="bg-white border border-gray-100 shadow-sm px-4 py-2 rounded-2xl rounded-bl-sm">
                  <span className="flex gap-1">
                    {[0, 1, 2].map((d) => (
                      <span
                        key={d}
                        className="w-2 h-2 rounded-full bg-primary-400 animate-bounce"
                        style={{ animationDelay: `${d * 0.15}s` }}
                      />
                    ))}
                  </span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Suggested questions */}
          {messages.length <= 1 && (
            <div className="px-3 pb-2 bg-gray-50 flex flex-wrap gap-1">
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-xs px-2 py-1 rounded-full border border-primary-200
                             text-primary-700 bg-primary-50 hover:bg-primary-100 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="px-3 py-2 border-t border-gray-100 bg-white flex gap-2 items-center">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
              placeholder="Nhập câu hỏi…"
              className="flex-1 text-sm px-3 py-2 rounded-full border border-gray-200
                         focus:outline-none focus:border-primary-400 bg-gray-50"
            />
            <button
              onClick={() => send()}
              disabled={!input.trim() || loading}
              className="w-9 h-9 rounded-full bg-primary-600 text-white flex items-center justify-center
                         disabled:opacity-40 hover:bg-primary-700 transition-colors flex-shrink-0"
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
}

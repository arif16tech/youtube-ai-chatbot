import { useEffect, useRef } from "react";
import { MessageCircle } from "lucide-react";
import MessageBubble from "./MessageBubble.jsx";
import ChatInput from "./ChatInput.jsx";

export default function ChatWindow({ messages, onSend, isBusy }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  return (
    <div className="flex h-full flex-col rounded-3xl glass-panel shadow-sm">
      <div className="flex items-center gap-3 border-b border-white/20 bg-white/40 px-5 py-4 backdrop-blur-md rounded-t-3xl">
        <div className="rounded-full bg-brand-100 p-2">
          <MessageCircle className="h-5 w-5 text-brand-600" />
        </div>
        <h2 className="text-base font-bold text-slate-800">Ask about this video</h2>
      </div>

      <div className="thin-scroll flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-slate-500">
            <div className="rounded-full bg-white/50 p-4 shadow-sm border border-white/40">
              <MessageCircle className="h-8 w-8 text-brand-400" />
            </div>
            <div className="space-y-1">
              <p className="text-base font-semibold text-slate-700">No messages yet</p>
              <p className="text-sm">Ask a question below, or tap a suggested query above.</p>
            </div>
          </div>
        ) : (
          messages.map((m) => (
            <MessageBubble
              key={m.id}
              role={m.role}
              content={m.content}
              sources={m.sources}
              isStreaming={m.isStreaming}
            />
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={onSend} disabled={isBusy} />
    </div>
  );
}

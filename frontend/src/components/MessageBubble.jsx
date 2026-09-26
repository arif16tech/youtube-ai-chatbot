import ReactMarkdown from "react-markdown";
import { Bot, User, Clock } from "lucide-react";

export default function MessageBubble({ role, content, sources, isStreaming }) {
  const isUser = role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-brand-600 text-white" : "bg-slate-800 text-white"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className={`flex max-w-[80%] flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-3xl px-5 py-3 text-sm leading-relaxed shadow-sm ${
            isUser
              ? "rounded-tr-sm bg-linear-to-br from-brand-500 to-purple-600 text-white shadow-brand-500/30"
              : "rounded-tl-sm glass-panel text-slate-800"
          }`}
        >
          {isUser ? (
            <span className="whitespace-pre-wrap">{content}</span>
          ) : (
            <div className="md-content">
              <ReactMarkdown>{content || (isStreaming ? "" : "…")}</ReactMarkdown>
              {isStreaming && (
                <span className="ml-0.5 inline-flex gap-0.5 align-middle">
                  <span className="typing-dot inline-block h-1.5 w-1.5 rounded-full bg-slate-400" />
                  <span className="typing-dot inline-block h-1.5 w-1.5 rounded-full bg-slate-400 [animation-delay:0.15s]" />
                  <span className="typing-dot inline-block h-1.5 w-1.5 rounded-full bg-slate-400 [animation-delay:0.3s]" />
                </span>
              )}
            </div>
          )}
        </div>

        {!isUser && sources?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {sources.map((s, i) => (
              <span
                key={i}
                title={s.text}
                className="inline-flex cursor-default items-center gap-1 rounded-full bg-white/60 px-2.5 py-1 text-[11px] font-semibold text-slate-600 shadow-sm border border-white/40"
              >
                <Clock className="h-3 w-3 text-brand-500" />
                {s.timestamp}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

import { useState } from "react";
import { Send } from "lucide-react";

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState("");

  const submit = (e) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      submit(e);
    }
  };

  return (
    <form onSubmit={submit} className="flex items-end gap-3 border-t border-white/20 bg-white/40 p-4 backdrop-blur-md rounded-b-3xl">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={1}
        placeholder="Ask a question about this video, in Hindi or English…"
        disabled={disabled}
        className="max-h-32 min-h-11 flex-1 resize-none rounded-2xl glass-input px-4 py-3 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/40 transition-all disabled:opacity-60"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-linear-to-r from-brand-600 to-brand-500 text-white shadow-md shadow-brand-500/20 transition-all hover:scale-105 active:scale-95 disabled:pointer-events-none disabled:opacity-40"
        aria-label="Send message"
      >
        <Send className="h-4 w-4" />
      </button>
    </form>
  );
}

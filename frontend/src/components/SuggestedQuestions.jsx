import { HelpCircle } from "lucide-react";

export default function SuggestedQuestions({ questions, onPick, disabled }) {
  if (!questions?.length) return null;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500">
        <HelpCircle className="h-4 w-4 text-slate-400" />
        Suggested queries
      </div>
      <div className="flex flex-wrap gap-2">
        {questions.map((q, i) => (
          <button
            key={i}
            type="button"
            disabled={disabled}
            onClick={() => onPick(q)}
            className="rounded-full glass-input px-4 py-2 text-left text-sm font-medium text-slate-700 shadow-sm transition-all hover:border-brand-400 hover:bg-brand-50 hover:text-brand-700 hover:scale-[1.02] active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

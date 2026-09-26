import { Clock, Languages, Sparkles } from "lucide-react";

export default function VideoPanel({ videoId, summary, language, isGenerated, durationSeconds }) {
  const mins = Math.floor(durationSeconds / 60);
  const secs = Math.round(durationSeconds % 60);

  return (
    <div className="flex flex-col gap-4">
      <div className="overflow-hidden rounded-2xl bg-black shadow-lg shadow-black/10 ring-1 ring-white/20">
        <div className="aspect-video w-full">
          <iframe
            className="h-full w-full"
            src={`https://www.youtube.com/embed/${videoId}`}
            title="YouTube video player"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-2 text-xs">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-white/60 px-3 py-1.5 font-medium text-slate-700 backdrop-blur-sm border border-white/40 shadow-sm">
          <Clock className="h-4 w-4 text-brand-500" />
          {mins}m {secs}s
        </span>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-white/60 px-3 py-1.5 font-medium text-slate-700 backdrop-blur-sm border border-white/40 shadow-sm">
          <Languages className="h-4 w-4 text-brand-500" />
          {language?.toUpperCase()} · {isGenerated ? "auto-generated" : "manual"} transcript
        </span>
      </div>

      <div className="rounded-2xl glass-panel p-5 shadow-sm">
        <div className="mb-3 flex items-center gap-2 text-base font-bold text-slate-800">
          <Sparkles className="h-5 w-5 text-brand-500" />
          AI Summary
        </div>
        <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">{summary}</p>
      </div>
    </div>
  );
}

import { useState } from "react";
import { Loader2, Youtube } from "lucide-react";

export default function UrlForm({ onSubmit, isLoading, error }) {
  const [url, setUrl] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url.trim() || isLoading) return;
    onSubmit(url.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="w-full relative group">
      <div className="absolute -inset-0.5 bg-linear-to-r from-brand-500 to-purple-600 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
      <div className="relative flex items-center gap-2 rounded-2xl glass-input p-2 shadow-sm focus-within:ring-2 focus-within:ring-brand-500/40 transition-all duration-300">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-50 ml-1">
          <Youtube className="h-6 w-6 text-red-500" />
        </div>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Paste a YouTube URL (Hindi or English video)…"
          className="flex-1 min-w-0 bg-transparent px-3 py-2 text-base text-slate-800 placeholder:text-slate-400 focus:outline-none"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !url.trim()}
          className="flex items-center gap-2 rounded-xl bg-linear-to-r from-brand-600 to-brand-500 px-5 py-2.5 text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98] hover:shadow-md disabled:pointer-events-none disabled:opacity-50"
        >
          {isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Processing…
            </>
          ) : (
            "Analyze Video"
          )}
        </button>
      </div>
      {error && (
        <p className="mt-3 px-2 text-sm font-medium text-red-500 flex items-center gap-1" role="alert">
          <span className="h-1.5 w-1.5 rounded-full bg-red-500 inline-block" /> {error}
        </p>
      )}
    </form>
  );
}

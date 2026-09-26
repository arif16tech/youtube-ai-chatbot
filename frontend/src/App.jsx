import { useCallback, useState } from "react";
import { Sparkles, AlertTriangle } from "lucide-react";
import UrlForm from "./components/UrlForm.jsx";
import VideoPanel from "./components/VideoPanel.jsx";
import SuggestedQuestions from "./components/SuggestedQuestions.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import { processVideo, streamQuestion, ApiError } from "./api.js";

let idCounter = 0;
const nextId = () => `msg-${Date.now()}-${idCounter++}`;

export default function App() {
  const [video, setVideo] = useState(null); // ProcessVideoResponse
  const [messages, setMessages] = useState([]);
  const [loadError, setLoadError] = useState("");
  const [isLoadingVideo, setIsLoadingVideo] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [suggested, setSuggested] = useState([]);

  const handleLoadVideo = useCallback(async (url) => {
    setIsLoadingVideo(true);
    setLoadError("");
    try {
      const data = await processVideo(url);
      setVideo(data);
      setSuggested(data.suggested_questions || []);
      setMessages([]);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Something went wrong while processing this video. Please try again.";
      setLoadError(message);
      setVideo(null);
    } finally {
      setIsLoadingVideo(false);
    }
  }, []);

  const handleSend = useCallback(
    async (question) => {
      if (!video) return;

      const userMsg = { id: nextId(), role: "user", content: question };
      const assistantId = nextId();
      const assistantMsg = {
        id: assistantId,
        role: "assistant",
        content: "",
        sources: [],
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsAsking(true);

      const updateAssistant = (patch) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? { ...m, ...patch(m) } : m))
        );
      };

      try {
        await streamQuestion(video.session_id, question, {
          onSources: (sources) => updateAssistant(() => ({ sources })),
          onToken: (text) =>
            updateAssistant((m) => ({ content: (m.content || "") + text })),
          onDone: () => updateAssistant(() => ({ isStreaming: false })),
          onError: (message) =>
            updateAssistant(() => ({
              content: `⚠️ ${message || "Failed to get an answer. Please try again."}`,
              isStreaming: false,
            })),
        });
      } catch {
        updateAssistant(() => ({
          content: "⚠️ Failed to get an answer. Please try again.",
          isStreaming: false,
        }));
      } finally {
        setIsAsking(false);
      }
    },
    [video]
  );

  return (
    <div className="mx-auto flex h-screen max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8 overflow-hidden">
      <header className="flex shrink-0 items-center gap-3">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-linear-to-br from-brand-500 to-purple-600 text-white shadow-lg shadow-brand-500/30">
          <Sparkles className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-xl font-extrabold tracking-tight text-slate-900">
            YouTube AI Chatbot
          </h1>
          <p className="text-sm font-medium text-slate-500">
            RAG over YouTube transcripts · Hindi &amp; English
          </p>
        </div>
      </header>

      <div className="shrink-0">
        <UrlForm onSubmit={handleLoadVideo} isLoading={isLoadingVideo} error={loadError} />
      </div>

      {!video && !isLoadingVideo && (
        <div className="flex flex-1 flex-col items-center justify-center gap-6 rounded-3xl glass-panel p-8 text-center sm:p-16 mb-4">
          <div className="rounded-full bg-brand-100 p-4">
            <Sparkles className="h-10 w-10 text-brand-600" />
          </div>
          <div className="max-w-md space-y-2">
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight">Unlock YouTube Insights</h2>
            <p className="text-slate-600 text-lg">
              Paste a video URL above. Our AI digests the transcript so you can ask questions and get instant, accurate answers.
            </p>
          </div>
        </div>
      )}

      {video && (
        <div className="grid flex-1 min-h-0 grid-cols-1 gap-6 lg:grid-cols-5 pb-4">
          <div className="flex flex-col gap-4 lg:col-span-2 overflow-y-auto thin-scroll pr-2 glass-panel p-4 rounded-2xl">
            <VideoPanel
              videoId={video.video_id}
              summary={video.summary}
              language={video.language}
              isGenerated={video.is_generated}
              durationSeconds={video.duration_seconds}
            />
            <SuggestedQuestions
              questions={suggested}
              onPick={handleSend}
              disabled={isAsking}
            />
          </div>

          <div className="lg:col-span-3 flex flex-col min-h-0">
            <div className="flex-1 min-h-0">
              <ChatWindow messages={messages} onSend={handleSend} isBusy={isAsking} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

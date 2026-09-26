const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function handleResponse(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || body.error || detail;
    } catch {
      // response wasn't JSON; keep default detail
    }
    throw new ApiError(detail, res.status);
  }
  return res.json();
}

export async function processVideo(url, preferredLanguages = ["hi", "en"]) {
  const res = await fetch(`${BASE_URL}/video/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, preferred_languages: preferredLanguages }),
  });
  return handleResponse(res);
}

export async function askQuestion(sessionId, question) {
  const res = await fetch(`${BASE_URL}/chat/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  });
  return handleResponse(res);
}

/**
 * Streams an answer via Server-Sent Events.
 * callbacks: { onSources(sources), onToken(text), onDone(), onError(message) }
 */
export async function streamQuestion(sessionId, question, callbacks) {
  const res = await fetch(`${BASE_URL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, question }),
  });

  if (!res.ok || !res.body) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || body.error || detail;
    } catch {
      // ignore
    }
    callbacks.onError?.(detail);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";

    for (const rawEvent of events) {
      const lines = rawEvent.split("\n");
      let eventType = "message";
      let data = "";
      for (const line of lines) {
        if (line.startsWith("event:")) eventType = line.slice(6).trim();
        if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) continue;
      try {
        const parsed = JSON.parse(data);
        if (eventType === "sources") callbacks.onSources?.(parsed);
        else if (eventType === "token") callbacks.onToken?.(parsed.text);
        else if (eventType === "error") callbacks.onError?.(parsed.error);
        else if (eventType === "done") callbacks.onDone?.();
      } catch {
        // partial/non-JSON payload; skip
      }
    }
  }
}

export { ApiError };

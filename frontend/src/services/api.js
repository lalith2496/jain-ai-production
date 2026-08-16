const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000";


export async function streamJainAI({
  message,
  mode = "quick",
  signal,
  onMetadata,
  onToken,
  onDone,
  onError,
}) {
  try {
    const response = await fetch(
      `${API_URL}/api/chat`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          message,
          mode,
        }),

        signal,
      },
    );

    if (!response.ok) {
      const data = await response
        .json()
        .catch(() => ({}));

      throw new Error(
        data.detail ||
          `Request failed: ${response.status}`,
      );
    }

    if (!response.body) {
      throw new Error(
        "Streaming response is unavailable.",
      );
    }

    const reader =
      response.body.getReader();

    const decoder =
      new TextDecoder();

    let buffer = "";
    let completed = false;

    while (true) {
      const {
        value,
        done,
      } = await reader.read();

      if (done) {
        break;
      }

      buffer += decoder.decode(
        value,
        {
          stream: true,
        },
      );

      const lines =
        buffer.split("\n");

      buffer =
        lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) {
          continue;
        }

        const event =
          JSON.parse(line);

        if (
          event.type ===
          "metadata"
        ) {
          onMetadata?.(event);
        }

        if (
          event.type ===
          "token"
        ) {
          onToken?.(
            event.content || "",
          );
        }

        if (
          event.type ===
           "done"
        ) {
           completed = true;
           onDone?.();
         }

        if (
          event.type ===
          "error"
        ) {
          throw new Error(
            event.message ||
              "Generation failed.",
          );
        }
      }
    }

    if (!completed) {
         onDone?.();
    }

  } catch (error) {

    if (
      error.name ===
      "AbortError"
    ) {
      return;
    }

    onError?.(error);

    throw error;
  }
}


export async function searchKnowledge(
  query,
) {
  const response = await fetch(
    `${API_URL}/api/search?q=${encodeURIComponent(
      query,
    )}`,
  );

  if (!response.ok) {
    throw new Error(
      "Knowledge search failed.",
    );
  }

  return response.json();
}
export async function getContent(type){const r=await fetch(`${API_URL}/api/content?type=${encodeURIComponent(type)}`);if(!r.ok)throw Error("Library unavailable");return r.json()}
export async function getContentItem(slug){const r=await fetch(`${API_URL}/api/content/${encodeURIComponent(slug)}`);if(!r.ok)throw Error("Content unavailable");return r.json()}

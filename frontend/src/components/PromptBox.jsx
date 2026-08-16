import React, { useState } from "react";
import { ArrowUp, Mic, Paperclip, Sparkles } from "lucide-react";
export default function PromptBox({
  onSubmit,
  large = false,
  initialValue = "",
  disabled = false,
}) {
  const [value, setValue] = useState("");
  const submit = () => {
    if (disabled) {
      return;
    }

    const next = value.trim();

    if (!next) {
      return;
    }

    onSubmit(next);

    setValue("");
  };
  return (
    <div className={large ? "prompt-box large" : "prompt-box"}>
      <div className="prompt-leading">
        <Sparkles size={18} />
      </div>
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            submit();
          }
        }}
        placeholder="Ask anything about Jainism..."
        rows={1}
      />
      <div className="prompt-actions">
        <button>
          <Paperclip size={18} />
        </button>
        <button>
          <Mic size={18} />
        </button>
        <button
          className="send-btn"
          onClick={submit}
          disabled={disabled}
          aria-label="Send"
        >
          <ArrowUp size={18} />
        </button>
      </div>
    </div>
  );
}

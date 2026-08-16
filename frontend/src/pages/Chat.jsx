import React, { useEffect, useRef, useState } from "react";

import { ArrowDown, Square } from "lucide-react";

import { streamJainAI } from "../services/api";

import PromptBox from "../components/PromptBox";
import LearningModes from "../components/LearningModes";
import AIOrb from "../components/AIOrb";
import AIAnswer from "../components/AIAnswer";

export default function Chat({
  initialPrompt,
  initialMessages = [],
  onMessagesChange,
}) {
  const [mode, setMode] = useState("quick");

  const [messages, setMessages] = useState(initialMessages);

  const [generating, setGenerating] = useState(false);

  const [showScrollButton, setShowScrollButton] = useState(false);

  const started = useRef(false);

  const abortController = useRef(null);

  const conversationRef = useRef(null);

  const bottomRef = useRef(null);

  const shouldFollow = useRef(true);

  // ===================================================
  // MESSAGE ID
  // ===================================================

  const createId = () => {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return crypto.randomUUID();
    }

    return Date.now().toString() + Math.random().toString(36).substring(2);
  };

  // ===================================================
  // SCROLL HELPERS
  // ===================================================

  const isNearBottom = () => {
    const container = conversationRef.current;

    if (!container) {
      return true;
    }

    const distance =
      container.scrollHeight - container.scrollTop - container.clientHeight;

    return distance < 180;
  };

  const scrollToBottom = (behavior = "smooth") => {
    bottomRef.current?.scrollIntoView({
      behavior,
      block: "end",
    });

    shouldFollow.current = true;

    setShowScrollButton(false);
  };

  // ===================================================
  // USER SCROLL
  // ===================================================

  const handleScroll = () => {
    const nearBottom = isNearBottom();

    shouldFollow.current = nearBottom;

    setShowScrollButton(!nearBottom);
  };

  // ===================================================
  // SMART STREAM FOLLOW
  // ===================================================

  useEffect(() => {
    if (generating && shouldFollow.current) {
      bottomRef.current?.scrollIntoView({
        behavior: "auto",
        block: "end",
      });
    }
  }, [messages, generating]);

  // ===================================================
  // HISTORY CALLBACK
  // ===================================================

  useEffect(() => {
    if (typeof onMessagesChange === "function") {
      onMessagesChange(messages);
    }
  }, [messages, onMessagesChange]);

  // ===================================================
  // STOP GENERATION
  // ===================================================

  const stopGeneration = () => {
    if (abortController.current) {
      abortController.current.abort();

      abortController.current = null;
    }

    setGenerating(false);

    setMessages((current) =>
      current.map((message) =>
        message.streaming
          ? {
              ...message,
              streaming: false,
              stopped: true,
            }
          : message,
      ),
    );
  };

  // ===================================================
  // SEND
  // ===================================================

  const send = async (prompt) => {
    const cleanPrompt = prompt.trim();

    if (!cleanPrompt || generating) {
      return;
    }

    // -------------------------------------------------
    // Give THIS AI response its own permanent ID.
    // -------------------------------------------------

    const assistantId = createId();

    const userId = createId();

    const userMessage = {
      id: userId,
      role: "user",
      text: cleanPrompt,
    };

    const assistantMessage = {
      id: assistantId,
      role: "ai",
      text: "",
      sources: [],
      streaming: true,
      stopped: false,
      error: false,
      mode,
    };

    // -------------------------------------------------
    // Add user + assistant placeholder together.
    // -------------------------------------------------

    setMessages((current) => [...current, userMessage, assistantMessage]);

    setGenerating(true);

    shouldFollow.current = true;

    setShowScrollButton(false);

    // Move to new question.
    setTimeout(() => {
      scrollToBottom("smooth");
    }, 40);

    const controller = new AbortController();

    abortController.current = controller;

    try {
      await streamJainAI({
        message: cleanPrompt,

        mode,

        signal: controller.signal,

        // ---------------------------------------------
        // Metadata / sources
        // ---------------------------------------------

        onMetadata: (metadata) => {
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId
                ? {
                    ...message,

                    sources: metadata.sources || [],
                  }
                : message,
            ),
          );
        },

        // ---------------------------------------------
        // Streaming token
        // ---------------------------------------------

        onToken: (token) => {
          if (!token) {
            return;
          }

          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId
                ? {
                    ...message,

                    text: (message.text || "") + token,
                  }
                : message,
            ),
          );
        },

        // ---------------------------------------------
        // Complete
        // ---------------------------------------------

        onDone: () => {
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantId
                ? {
                    ...message,
                    streaming: false,
                  }
                : message,
            ),
          );

          setGenerating(false);
        },

        // ---------------------------------------------
        // Error
        // ---------------------------------------------

        onError: (error) => {
          setMessages((current) =>
            current.map((message) => {
              if (message.id !== assistantId) {
                return message;
              }

              return {
                ...message,

                text:
                  message.text ||
                  "Jain AI could not " +
                    "complete this response. " +
                    error.message,

                streaming: false,

                error: true,
              };
            }),
          );

          setGenerating(false);
        },
      });
    } catch (error) {
      if (error.name !== "AbortError") {
        console.error("Jain AI error:", error);
      }
    } finally {
      abortController.current = null;

      setGenerating(false);
    }
  };

  // ===================================================
  // INITIAL PROMPT
  // ===================================================

  useEffect(() => {
    if (initialPrompt && !started.current) {
      started.current = true;

      send(initialPrompt);
    }
  }, [initialPrompt]);

  // ===================================================
  // UI
  // ===================================================

  return (
    <main className="chat-page">
      {/* =============================================
          HEADER
      ============================================== */}

      <div className="chat-header">
        <div>
          <div className="section-kicker">CONVERSATION</div>

          <h2>Explore with Jain AI</h2>
        </div>

        <LearningModes activeMode={mode} onChange={setMode} />
      </div>

      {/* =============================================
          CONVERSATION
      ============================================== */}

      <div
        className="conversation"
        ref={conversationRef}
        onScroll={handleScroll}
      >
        {messages.length === 0 && (
          <div className="chat-empty">
            <AIOrb compact />

            <h2>Ask something worth exploring.</h2>

            <p>Try a concept, story, person, scripture, place or practice.</p>
          </div>
        )}

        {messages.map((message) => {
          if (message.role === "user") {
            return (
              <div className="user-message" key={message.id}>
                <div className="user-chip">YOU</div>

                <div>{message.text}</div>
              </div>
            );
          }

          return (
            <AIAnswer
              key={message.id}
              message={message}
              mode={message.mode || "quick"}
            />
          );
        })}

        <div ref={bottomRef} className="chat-bottom-anchor" />
      </div>

      {/* =============================================
          FLOATING SCROLL DOWN
      ============================================== */}

      {showScrollButton && (
        <button
          type="button"
          className="scroll-bottom-btn"
          onClick={() => scrollToBottom("smooth")}
          aria-label="Go to latest response"
          title="Go to latest"
        >
          <ArrowDown size={20} />
        </button>
      )}

      {/* =============================================
          COMPOSER
      ============================================== */}

      <div className="chat-composer-wrap">
        {generating && (
          <div className="stop-generation-wrap">
            <button
              type="button"
              className="stop-generation-btn"
              onClick={stopGeneration}
            >
              <Square size={12} fill="currentColor" />
              Stop generating
            </button>
          </div>
        )}

        <PromptBox onSubmit={send} disabled={generating} />

        <div className="composer-note">
          Jain AI can make mistakes. Verify important details with approved
          sources.
        </div>
      </div>
    </main>
  );
}

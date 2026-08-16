import React from "react";

import {
  BookOpen,
  ChevronRight,
  ExternalLink,
  GitBranch,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

export default function AIAnswer({ message, mode = "quick" }) {
  // ---------------------------------------------------
  // Basic state
  // ---------------------------------------------------

  const text = message?.text || "";

  const hasAnswer = text.trim().length > 0;

  const isStreaming = message?.streaming === true;

  const isFinished = !isStreaming;

  const isError = message?.error === true;

  const wasStopped = message?.stopped === true;

  // ---------------------------------------------------
  // Remove duplicate sources
  // ---------------------------------------------------

  const uniqueSources = Array.from(
    new Map(
      (message?.sources || []).map((source) => [
        source.url || source.title,
        source,
      ]),
    ).values(),
  );

  // ---------------------------------------------------
  // Mode label
  // ---------------------------------------------------

  const modeLabels = {
    quick: "quick",
    deep: "deep dive",
    story: "story",
    study: "study",
  };

  const modeLabel = modeLabels[mode] || mode;

  // ---------------------------------------------------
  // Semantic match formatter
  // ---------------------------------------------------

  const formatSimilarity = (similarity) => {
    if (similarity === undefined || similarity === null) {
      return null;
    }

    let value = Number(similarity);

    if (Number.isNaN(value)) {
      return null;
    }

    // Backend usually returns 0-1.
    // Handle 0-100 as well.
    if (value <= 1) {
      value = value * 100;
    }

    value = Math.round(Math.max(0, Math.min(value, 100)));

    return `${value}% semantic match`;
  };

  return (
    <section
      className={`ai-answer ${isStreaming ? "is-streaming" : ""} ${
        isError ? "has-error" : ""
      }`}
    >
      {/* ---------------------------------------------
          Jain AI identity
      --------------------------------------------- */}

      <div className="ai-answer-header">
        <div className="ai-answer-avatar">
          <Sparkles size={22} />
        </div>

        <div className="ai-answer-identity">
          <div className="ai-answer-name">JAIN AI</div>

          <div className="ai-answer-meta">
            <ShieldCheck size={16} />

            <span>Knowledge-grounded</span>

            <span className="ai-meta-dot">·</span>

            <span>{modeLabel}</span>
          </div>
        </div>
      </div>

      {/* ---------------------------------------------
          Waiting for first token
      --------------------------------------------- */}

      {isStreaming && !hasAnswer && (
        <div className="ai-generating">
          <div className="ai-generating-orb">
            <Sparkles size={17} />
          </div>

          <span>Exploring approved Jain knowledge</span>

          <div className="ai-generating-dots">
            <span />
            <span />
            <span />
          </div>
        </div>
      )}

      {/* ---------------------------------------------
          Actual answer

          This appears as soon as streaming tokens arrive.
      --------------------------------------------- */}

      {hasAnswer && (
        <div
          className={`ai-answer-content ${isError ? "ai-answer-error" : ""}`}
        >
          {/*
            white-space: pre-wrap in CSS
            will preserve headings/newlines
            returned by Ollama.
          */}

          {text}

          {isStreaming && (
            <span className="streaming-cursor" aria-hidden="true" />
          )}
        </div>
      )}

      {/* ---------------------------------------------
          Stopped generation indicator
      --------------------------------------------- */}

      {wasStopped && hasAnswer && (
        <div className="generation-stopped">Generation stopped</div>
      )}

      {/* ---------------------------------------------
          IMPORTANT

          Everything below appears ONLY AFTER
          answer generation finishes.
      --------------------------------------------- */}

      {isFinished && hasAnswer && !isError && (
        <>
          {/* -----------------------------------------
              Explore section
          ----------------------------------------- */}

          <div className="answer-explore">
            <div className="answer-explore-label">
              <BookOpen size={19} />

              <span>Explore the concept</span>
            </div>

            <button type="button" className="explore-pill">
              Key ideas
              <ChevronRight size={17} />
            </button>

            <button type="button" className="explore-pill">
              Related teachings
              <ChevronRight size={17} />
            </button>

            <button type="button" className="explore-pill">
              <GitBranch size={18} />
              View connections
            </button>
          </div>

          {/* -----------------------------------------
              Sources

              Only render if actual sources exist.
          ----------------------------------------- */}

          {uniqueSources.length > 0 && (
            <div className="answer-sources">
              <div className="sources-heading">SOURCES</div>

              <div className="source-grid">
                {uniqueSources.map((source, index) => {
                  const similarity = formatSimilarity(source.similarity);

                  return (
                    <a
                      key={source.url || `${source.title}-${index}`}
                      className="source-card"
                      href={source.url || undefined}
                      target={source.url ? "_blank" : undefined}
                      rel={source.url ? "noreferrer" : undefined}
                    >
                      <div className="source-check">
                        <ShieldCheck size={20} />
                      </div>

                      <div className="source-info">
                        <div className="source-approved">APPROVED SOURCE</div>

                        <div className="source-title">
                          {source.title || "Jain AI Source"}
                        </div>

                        {similarity && (
                          <div className="source-match">{similarity}</div>
                        )}
                      </div>

                      {source.url && (
                        <ExternalLink className="source-external" size={20} />
                      )}
                    </a>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </section>
  );
}

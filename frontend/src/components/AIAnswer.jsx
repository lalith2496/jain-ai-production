import React from "react";
import {
  BookOpen,
  ChevronRight,
  ExternalLink,
  GitBranch,
  ShieldCheck,
  Sparkles,
  Video,
  Globe2,
} from "lucide-react";

export default function AIAnswer({ message, mode = "quick" }) {
  const text = message?.text || "";
  const hasAnswer = text.trim().length > 0;
  const isStreaming = message?.streaming === true;
  const isFinished = !isStreaming;
  const isError = message?.error === true;
  const wasStopped = message?.stopped === true;

  const uniqueSources = Array.from(
    new Map(
      (message?.sources || []).map((source) => [
        source.url || source.title,
        source,
      ]),
    ).values(),
  );

  const modeLabels = {
    quick: "quick",
    deep: "deep dive",
    story: "story",
    study: "study",
  };

  const formatSimilarity = (similarity) => {
    if (similarity === undefined || similarity === null) return null;
    let value = Number(similarity);
    if (Number.isNaN(value)) return null;
    if (value <= 1) value *= 100;
    return `${Math.round(Math.max(0, Math.min(value, 100)))}% semantic match`;
  };

  const sourceLabel = (source) => {
    if (source.trust_status === "approved") return "APPROVED SOURCE";
    if (source.source_type === "youtube") return "YOUTUBE RESULT";
    return "LIVE WEB SOURCE";
  };

  const SourceIcon = ({ source }) => {
    if (source.source_type === "youtube") {
      return <Video size={20} />;
    }

    if (source.trust_status === "approved") {
      return <ShieldCheck size={20} />;
    }

    return <Globe2 size={20} />;
  };

  return (
    <section
      className={`ai-answer ${isStreaming ? "is-streaming" : ""} ${
        isError ? "has-error" : ""
      }`}
    >
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
            <span>{modeLabels[mode] || mode}</span>
          </div>
        </div>
      </div>

      {isStreaming && !hasAnswer && (
        <div className="ai-generating">
          <div className="ai-generating-orb">
            <Sparkles size={17} />
          </div>
          <span>Searching Jain knowledge and live sources</span>
          <div className="ai-generating-dots">
            <span />
            <span />
            <span />
          </div>
        </div>
      )}

      {hasAnswer && (
        <div
          className={`ai-answer-content ${isError ? "ai-answer-error" : ""}`}
        >
          {text}
          {isStreaming && (
            <span className="streaming-cursor" aria-hidden="true" />
          )}
        </div>
      )}

      {wasStopped && hasAnswer && (
        <div className="generation-stopped">Generation stopped</div>
      )}

      {isFinished && hasAnswer && !isError && (
        <>
          <div className="answer-explore">
            <div className="answer-explore-label">
              <BookOpen size={19} />
              <span>Explore the concept</span>
            </div>

            <button type="button" className="explore-pill">
              Key ideas <ChevronRight size={17} />
            </button>

            <button type="button" className="explore-pill">
              Related teachings <ChevronRight size={17} />
            </button>

            <button type="button" className="explore-pill">
              <GitBranch size={18} />
              View connections
            </button>
          </div>

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
                        <SourceIcon source={source} />
                      </div>

                      <div className="source-info">
                        <div className="source-approved">
                          {sourceLabel(source)}
                        </div>

                        <div className="source-title">
                          {source.title || "Jain AI Source"}
                        </div>

                        {similarity && (
                          <div className="source-match">{similarity}</div>
                        )}

                        {source.channel_title && (
                          <div className="source-match">
                            {source.channel_title}
                          </div>
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

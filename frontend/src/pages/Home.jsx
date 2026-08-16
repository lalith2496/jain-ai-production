import React, { useState } from "react";
import AIOrb from "../components/AIOrb";
import PromptBox from "../components/PromptBox";
import LearningModes from "../components/LearningModes";
import DiscoveryCard from "../components/DiscoveryCard";
import { Flower2, Mountain, Infinity, ScrollText } from "lucide-react";
const cards = [
  {
    eyebrow: "TIRTHANKARA",
    title: "Mahavira",
    description:
      "Meet the 24th Tirthankara and explore the ideas that shaped Jain philosophy.",
    icon: <Flower2 size={24} />,
    prompt:
      "Tell me about Bhagwan Mahavira and why his teachings matter today.",
  },
  {
    eyebrow: "SACRED PLACE",
    title: "Girnar",
    description:
      "Explore one of Jainism's most sacred mountains and its connection to Neminath.",
    icon: <Mountain size={24} />,
    prompt: "Tell me the Jain significance of Girnar and Bhagwan Neminath.",
  },
  {
    eyebrow: "PHILOSOPHY",
    title: "Anekantavada",
    description:
      "One truth, many viewpoints. Understand one of Jainism's most powerful ideas.",
    icon: <Infinity size={24} />,
    prompt:
      "Explain Anekantavada in a simple Gen-Z friendly way with examples.",
  },
  {
    eyebrow: "PRAYER",
    title: "Navkar Mantra",
    description:
      "Go beyond memorization and understand the deeper meaning of Jainism's core mantra.",
    icon: <ScrollText size={24} />,
    prompt: "Explain the meaning and significance of the Navkar Mantra.",
  },
];
export default function Home({ onStartChat }) {
  const [mode, setMode] = useState("quick");
  const start = (prompt) => {
    onStartChat(prompt);
  };
  return (
    <main className="home-page">
      <section className="hero-section">
        <div className="hero-badge">
          <span className="live-dot" />
          AI KNOWLEDGE GUIDE
        </div>
        <AIOrb />
        <h1>
          Ancient wisdom.
          <br />
          <span>New perspective.</span>
        </h1>
        <p className="hero-copy">
          Explore Jain philosophy, stories, scriptures, sacred places and
          everyday wisdom — powered by trusted knowledge.
        </p>
        <div className="hero-prompt">
          <PromptBox large onSubmit={start} />
        </div>
        <LearningModes activeMode={mode} onChange={setMode} />
      </section>
      <section className="journeys-section">
        <div className="section-heading-row">
          <div>
            <div className="section-kicker">START A JOURNEY</div>
            <h2>Discover Jainism your way</h2>
          </div>
          <span className="section-caption">
            Curated paths for curious minds
          </span>
        </div>
        <div className="discovery-grid">
          {cards.map((c) => (
            <DiscoveryCard key={c.title} {...c} onOpen={start} />
          ))}
        </div>
      </section>
      <section className="trending-section">
        <div className="section-kicker">TRENDING JOURNEYS</div>
        <div className="topic-pills">
          {[
            "Ahimsa",
            "Karma",
            "Paryushan",
            "Shatrunjaya",
            "Jain food",
            "24 Tirthankaras",
            "Aparigraha",
          ].map((t) => (
            <button key={t} onClick={() => start(`Teach me about ${t}.`)}>
              {t}
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}

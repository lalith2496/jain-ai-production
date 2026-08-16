import React, { useEffect, useState } from "react";

import Home from "./pages/Home";
import Chat from "./pages/Chat";
import Navbar from "./components/Navbar";
import HistorySidebar from "./components/HistorySidebar";
import Library from "./pages/Library";
import ContentCollection from "./pages/ContentCollection";
import Reader from "./pages/Reader";

import { getHistory, saveHistory } from "./services/history";

export default function App() {
  // ===================================================
  // PAGE
  // ===================================================

  const [activePage, setActivePage] = useState("home");

  // ===================================================
  // HISTORY
  // ===================================================

  const [conversations, setConversations] = useState(() => getHistory());

  const [activeConversationId, setActiveConversationId] = useState(null);

  const [initialPrompt, setInitialPrompt] = useState("");
  const [readerSlug,setReaderSlug]=useState("");
  const [readerFrom,setReaderFrom]=useState("library");

  // ===================================================
  // SAVE HISTORY
  // ===================================================

  useEffect(() => {
    saveHistory(conversations);
  }, [conversations]);

  // ===================================================
  // CURRENT CONVERSATION
  // ===================================================

  const activeConversation = conversations.find(
    (conversation) => conversation.id === activeConversationId,
  );

  // ===================================================
  // CREATE ID
  // ===================================================

  const createId = () => {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return crypto.randomUUID();
    }

    return Date.now().toString() + Math.random().toString(36).substring(2);
  };

  // ===================================================
  // TITLE
  // ===================================================

  const makeTitle = (prompt) => {
    if (!prompt?.trim()) {
      return "New conversation";
    }

    const clean = prompt.trim();

    if (clean.length <= 40) {
      return clean;
    }

    return clean.substring(0, 40) + "...";
  };

  // ===================================================
  // DATE
  // ===================================================

  const currentTime = () => {
    return new Date().toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  // ===================================================
  // START CHAT FROM HOME
  // ===================================================

  const startChat = (prompt = "") => {
    const id = createId();

    const conversation = {
      id,
      title: makeTitle(prompt),

      messages: [],

      createdAt: currentTime(),

      updatedAt: currentTime(),
    };

    setConversations((current) => [conversation, ...current]);

    setActiveConversationId(id);

    setInitialPrompt(prompt);

    setActivePage("chat");
  };

  // ===================================================
  // NEW CHAT
  // ===================================================

  const newChat = () => {
    startChat("");
  };

  // ===================================================
  // OPEN HISTORY ITEM
  // ===================================================

  const openConversation = (id) => {
    setActiveConversationId(id);

    // Important:
    // Don't send the old question again.
    setInitialPrompt("");

    setActivePage("chat");
  };

  // ===================================================
  // DELETE HISTORY ITEM
  // ===================================================

  const deleteConversation = (id) => {
    setConversations((current) =>
      current.filter((conversation) => conversation.id !== id),
    );

    // If current conversation deleted
    if (activeConversationId === id) {
      setActiveConversationId(null);

      setInitialPrompt("");

      setActivePage("home");
    }
  };

  // ===================================================
  // CHAT MESSAGE CHANGE
  // ===================================================

  const handleMessagesChange = (messages) => {
    if (!activeConversationId) {
      return;
    }

    setConversations((current) =>
      current.map((conversation) => {
        if (conversation.id !== activeConversationId) {
          return conversation;
        }

        // Find first user question
        const firstUserMessage = messages.find(
          (message) => message.role === "user",
        );

        const title = firstUserMessage
          ? makeTitle(firstUserMessage.text)
          : conversation.title;

        return {
          ...conversation,

          title,

          messages,

          updatedAt: currentTime(),
        };
      }),
    );
  };

  // ===================================================
  // NAVIGATION
  // ===================================================

  const navigate = (page) => {
    if (page === "home") {
      setActivePage("home");

      return;
    }

    setActivePage(page);
  };

  // ===================================================
  // UI
  // ===================================================

  return (
    <div className="app-shell">
      {/* Ambient AI background */}

      <div className="ambient ambient-one" />

      <div className="ambient ambient-two" />

      {/* Navigation */}

      <Navbar
        activePage={activePage}
        onNavigate={navigate}
        onNewChat={newChat}
      />

      {/* =============================================
          CHAT + HISTORY
      ============================================== */}

      {activePage === "chat" ? (
        <div className="chat-layout">
          <HistorySidebar
            conversations={conversations}
            activeId={activeConversationId}
            onSelect={openConversation}
            onNewChat={newChat}
            onDelete={deleteConversation}
          />

          <div className="chat-main">
            <Chat
              /*
               * Key is VERY important.
               *
               * Selecting another history item
               * remounts Chat with that
               * conversation's messages.
               */
              key={activeConversationId}
              initialPrompt={initialPrompt}
              initialMessages={activeConversation?.messages || []}
              onMessagesChange={handleMessagesChange}
            />
          </div>
        </div>
      ) : (
        /* =============================================
           HOME
        ============================================== */

        activePage === "library" ? <Library onOpen={(z)=>{setReaderSlug(z);setReaderFrom("library");setActivePage("reader")}} onAsk={startChat}/> : activePage === "stories" ? <ContentCollection type="story" onOpen={(z)=>{setReaderSlug(z);setReaderFrom("stories");setActivePage("reader")}}/> : activePage === "history" ? <ContentCollection type="history" onOpen={(z)=>{setReaderSlug(z);setReaderFrom("history");setActivePage("reader")}}/> : activePage === "reader" ? <Reader slug={readerSlug} onBack={()=>setActivePage(readerFrom)} onAsk={startChat}/> : <Home onStartChat={startChat} />
      )}
    </div>
  );
}

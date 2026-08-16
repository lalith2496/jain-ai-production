import {
  MessageSquare,
  Plus,
  Trash2,
} from "lucide-react";

export default function HistorySidebar({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
}) {
  return (
    <aside className="history-sidebar">
      <div className="history-top">
        <div className="history-title">
          HISTORY
        </div>

        <button
          className="new-chat-btn"
          onClick={onNewChat}
        >
          <Plus size={16} />
          New chat
        </button>
      </div>

      <div className="history-list">
        {conversations.length === 0 && (
          <div className="history-empty">
            Your conversations will appear here.
          </div>
        )}

        {conversations.map(
          (conversation) => (
            <button
              key={conversation.id}
              className={`history-item ${
                activeId === conversation.id
                  ? "active"
                  : ""
              }`}
              onClick={() =>
                onSelect(conversation.id)
              }
            >
              <MessageSquare size={15} />

              <div className="history-item-content">
                <div className="history-item-title">
                  {conversation.title}
                </div>

                <div className="history-item-time">
                  {conversation.updatedAt}
                </div>
              </div>

              <span
                className="history-delete"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(conversation.id);
                }}
              >
                <Trash2 size={14} />
              </span>
            </button>
          ),
        )}
      </div>
    </aside>
  );
}

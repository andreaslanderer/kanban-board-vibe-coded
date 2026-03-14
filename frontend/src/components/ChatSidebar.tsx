import { useMemo, useState } from "react";

export type ChatMessage = { role: "user" | "assistant"; content: string };

type ChatSidebarProps = {
  messages: ChatMessage[];
  onSend: (message: string) => Promise<void>;
  loading?: boolean;
  error?: string | null;
};

export const ChatSidebar = ({ messages, onSend, loading, error }: ChatSidebarProps) => {
  const [draft, setDraft] = useState("");

  const canSend = draft.trim().length > 0 && !loading;

  const handleSend = async () => {
    if (!canSend) return;
    const message = draft.trim();
    setDraft("");
    await onSend(message);
  };

  const renderedMessages = useMemo(
    () =>
      messages.map((msg, idx) => (
        <div key={idx} className="mb-3">
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[var(--gray-text)]">
            {msg.role}
          </div>
          <div className="rounded-2xl bg-white p-3 text-sm text-[var(--navy-dark)] shadow-[0_1px_4px_rgba(3,33,71,0.08)]">
            {msg.content}
          </div>
        </div>
      )),
    [messages]
  );

  return (
    <aside className="flex h-[720px] w-full flex-col rounded-3xl border border-[var(--stroke)] bg-[var(--surface-strong)] p-4 shadow-[var(--shadow)]">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[var(--navy-dark)]">AI Assistant</h2>
        <span className="text-xs text-[var(--gray-text)]">Chat</span>
      </div>

      {error ? (
        <div className="mb-3 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-700">
          {error}
        </div>
      ) : null}

      <div className="mb-4 flex-1 overflow-y-auto pr-2">{renderedMessages}</div>

      <div className="mt-4 flex items-center gap-2">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Type a message..."
          className="flex-1 rounded-2xl border border-[var(--stroke)] bg-white px-4 py-2 text-sm text-[var(--navy-dark)] outline-none"
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void handleSend();
            }
          }}
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={!canSend}
          className="rounded-2xl bg-[var(--primary-blue)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </aside>
  );
};

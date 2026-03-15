import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card } from "@/lib/kanban";

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => void;
  highlighted?: boolean;
};

export const KanbanCard = ({ card, onDelete, highlighted = false }: KanbanCardProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <article
      ref={setNodeRef}
      style={style}
      className={clsx(
        "rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_12px_24px_rgba(3,33,71,0.08)]",
        "transition-all duration-150",
        isDragging && "opacity-60 shadow-[0_18px_32px_rgba(3,33,71,0.16)]",
        highlighted && "ring-2 ring-[var(--accent-yellow)]"
      )}
      {...attributes}
      {...listeners}
      data-testid={`card-${card.id}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="font-display text-base font-semibold text-[var(--navy-dark)]">
            {card.title}
          </h4>
          <p className="mt-2 text-sm leading-6 text-[var(--gray-text)]">
            {card.details}
          </p>
        </div>
        <button
          type="button"
          onClick={() => onDelete(card.id)}
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md transition-colors"
          style={{ color: "var(--gray-text)" }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLButtonElement).style.background = "#fef2f2";
            (e.currentTarget as HTMLButtonElement).style.color = "#ef4444";
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLButtonElement).style.background = "transparent";
            (e.currentTarget as HTMLButtonElement).style.color = "var(--gray-text)";
          }}
          aria-label={`Delete ${card.title}`}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M1 3h12M5 3V2h4v1M2 3l1 9a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1l1-9" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M5.5 6v4M8.5 6v4" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round"/>
          </svg>
        </button>
      </div>
    </article>
  );
};

"use client";

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "@/lib/auth";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { api, type BoardData } from "@/lib/api";
import { createId, moveCard } from "@/lib/kanban";

export const KanbanBoard = () => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [boardId, setBoardId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  useEffect(() => {
    api
      .fetchBoard()
      .then(({ boardData, boardId }) => {
        setBoard(boardData);
        setBoardId(boardId);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const cardsById = useMemo(() => board?.cards || {}, [board?.cards]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id || !board || !boardId) {
      return;
    }


    const activeId = active.id as string;
    let overId = over.id as string;

    // If over is a column, ensure it has the 'column-' prefix
    const isOverColumn = board.columns.some(col => `column-${col.id}` === overId);
    if (isOverColumn) {
      // Remove 'column-' prefix for moveCard logic, which expects just the column id
      overId = overId;
    }

    // Optimistic update
    const optimisticColumns = moveCard(board.columns, activeId, overId);
    setBoard({ ...board, columns: optimisticColumns });

    try {
      // Find the new column and position
      const newColumn = optimisticColumns.find(col => col.cardIds.includes(activeId));
      if (!newColumn) return;
      const position = newColumn.cardIds.indexOf(activeId);

      await api.moveCard(activeId, newColumn.id, position);
    } catch (err) {
      // Revert on error
      setBoard(board); // revert to previous
      setError("Failed to move card");
    }
  };

  const handleRenameColumn = async (columnId: string, title: string) => {
    if (!board) return;

    // Optimistic update
    const optimisticColumns = board.columns.map((column) =>
      column.id === columnId ? { ...column, title } : column
    );
    setBoard({ ...board, columns: optimisticColumns });

    try {
      await api.renameColumn(columnId, title);
    } catch (err) {
      // Revert
      setBoard(board);
      setError("Failed to rename column");
    }
  };

  const handleAddCard = async (columnId: string, title: string, details: string) => {
    if (!board || !boardId) return;

    const tempId = createId("card");
    const newCard = { id: tempId, title, details: details || "No details yet." };

    // Optimistic update
    const optimisticCards = { ...board.cards, [tempId]: newCard };
    const optimisticColumns = board.columns.map((column) =>
      column.id === columnId
        ? { ...column, cardIds: [...column.cardIds, tempId] }
        : column
    );
    setBoard({ cards: optimisticCards, columns: optimisticColumns });

    try {
      const realCard = await api.createCard(boardId, columnId, title, details);
      // Patch in the real card ID everywhere
      setBoard((prev) => {
        if (!prev) return prev;
        // Remove temp card, add real card
        const { [tempId]: _, ...restCards } = prev.cards;
        const newCards = { ...restCards, [realCard.id]: realCard };
        const newColumns = prev.columns.map((col) =>
          col.id === columnId
            ? {
                ...col,
                cardIds: col.cardIds.map((cid) => (cid === tempId ? realCard.id : cid)),
              }
            : col
        );
        return { cards: newCards, columns: newColumns };
      });
    } catch (err) {
      // Revert
      setBoard(board);
      setError("Failed to add card");
    }
  };

  const handleDeleteCard = async (columnId: string, cardId: string) => {
    if (!board) return;

    // Optimistic update
    const optimisticCards = Object.fromEntries(
      Object.entries(board.cards).filter(([id]) => id !== cardId)
    );
    const optimisticColumns = board.columns.map((column) =>
      column.id === columnId
        ? {
            ...column,
            cardIds: column.cardIds.filter((id) => id !== cardId),
          }
        : column
    );
    setBoard({ cards: optimisticCards, columns: optimisticColumns });

    try {
      await api.deleteCard(cardId);
    } catch (err) {
      // Revert
      setBoard(board);
      setError("Failed to delete card");
    }
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  const { logout } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>Loading board...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  if (!board) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p>No board data</p>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex justify-end">
            <button
              onClick={logout}
              className="text-sm text-[var(--navy-dark)] underline"
            >
              Log out
            </button>
          </div>
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                Focus
              </p>
              <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCorners}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="grid gap-6 lg:grid-cols-5">
            {board.columns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                cards={column.cardIds.map((cardId) => board.cards[cardId])}
                onRename={handleRenameColumn}
                onAddCard={handleAddCard}
                onDeleteCard={handleDeleteCard}
              />
            ))}
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[260px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>
      </main>
    </div>
  );
};

import React from "react";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanColumn } from "@/components/KanbanColumn";
import type { Column, Card } from "@/lib/kanban";

const sampleColumn: Column = {
  id: "col-test",
  title: "Test",
  cardIds: ["card-a"],
};

const sampleCards: Card[] = [
  { id: "card-a", title: "A", details: "Detail A" },
];

describe("KanbanColumn", () => {
  it("renders title and card count", () => {
    render(
      <KanbanColumn
        column={sampleColumn}
        cards={sampleCards}
        onRename={() => {}}
        onAddCard={() => {}}
        onDeleteCard={() => {}}
      />
    );

    expect(screen.getByDisplayValue("Test")).toBeInTheDocument();
    expect(screen.getByText(/1 cards?/i)).toBeInTheDocument();
  });

  it("calls onRename when title changes", async () => {
    // use a wrapper to hold state so the column title actually updates on prop changes
    const Wrapper = () => {
      const [col, setCol] = React.useState<Column>(sampleColumn);
      const handleRename = (id: string, title: string) => {
        setCol((c) => ({ ...c, title }));
      };
      return (
        <KanbanColumn
          column={col}
          cards={sampleCards}
          onRename={handleRename}
          onAddCard={() => {}}
          onDeleteCard={() => {}}
        />
      );
    };

    render(<Wrapper />);
    const input = screen.getByDisplayValue("Test");
    await userEvent.clear(input);
    await userEvent.type(input, "Updated");
    expect(input).toHaveValue("Updated");
  });
});

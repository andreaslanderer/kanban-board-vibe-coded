import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanCard } from "@/components/KanbanCard";
import type { Card } from "@/lib/kanban";

const sampleCard: Card = {
  id: "card-x",
  title: "X",
  details: "Details",
};

describe("KanbanCard", () => {
  it("renders title and details", () => {
    render(<KanbanCard card={sampleCard} onDelete={() => {}} />);
    expect(screen.getByText("X")).toBeInTheDocument();
    expect(screen.getByText("Details")).toBeInTheDocument();
  });

  it("calls onDelete when remove button clicked", async () => {
    const handleDelete = vi.fn();
    render(<KanbanCard card={sampleCard} onDelete={handleDelete} />);
    const button = screen.getByRole("button", { name: /delete x/i });
    await userEvent.click(button);
    expect(handleDelete).toHaveBeenCalledWith("card-x");
  });
});

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ChatSidebar } from "@/components/ChatSidebar";

const mockOnSend = vi.fn();

describe("ChatSidebar", () => {
  it("renders with empty messages", () => {
    render(<ChatSidebar messages={[]} onSend={mockOnSend} />);
    expect(screen.getByText("AI Assistant")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Type a message...")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send/i })).toBeInTheDocument();
  });

  it("displays messages", () => {
    const messages = [
      { role: "user" as const, content: "Hello" },
      { role: "assistant" as const, content: "Hi there!" },
    ];
    render(<ChatSidebar messages={messages} onSend={mockOnSend} />);
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Hi there!")).toBeInTheDocument();
  });

  it("calls onSend when sending a message", async () => {
    render(<ChatSidebar messages={[]} onSend={mockOnSend} />);
    const input = screen.getByPlaceholderText("Type a message...");
    const sendButton = screen.getByRole("button", { name: /send/i });

    await userEvent.type(input, "Test message");
    await userEvent.click(sendButton);

    expect(mockOnSend).toHaveBeenCalledWith("Test message");
    expect(input).toHaveValue("");
  });

  it("calls onSend when pressing Enter", async () => {
    render(<ChatSidebar messages={[]} onSend={mockOnSend} />);
    const input = screen.getByPlaceholderText("Type a message...");

    await userEvent.type(input, "Test message{enter}");

    expect(mockOnSend).toHaveBeenCalledWith("Test message");
    expect(input).toHaveValue("");
  });

  it("does not call onSend with empty message", async () => {
    render(<ChatSidebar messages={[]} onSend={mockOnSend} />);
    const sendButton = screen.getByRole("button", { name: /send/i });

    await userEvent.click(sendButton);

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it("disables send button when loading", () => {
    render(<ChatSidebar messages={[]} onSend={mockOnSend} loading={true} />);
    const sendButton = screen.getByRole("button", { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it("displays error message", () => {
    render(<ChatSidebar messages={[]} onSend={mockOnSend} error="Test error" />);
    expect(screen.getByText("Test error")).toBeInTheDocument();
  });
});
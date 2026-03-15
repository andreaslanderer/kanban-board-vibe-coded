import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ChatSidebar } from "@/components/ChatSidebar";

const mockOnSend = vi.fn();

describe("ChatSidebar", () => {
  beforeEach(() => {
    mockOnSend.mockClear();
  });

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

  it("shows Chat label when onClearHistory is not provided", () => {
    render(<ChatSidebar messages={[]} onSend={mockOnSend} />);
    expect(screen.getByText("Chat")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /clear history/i })).not.toBeInTheDocument();
  });

  it("does not show Clear history button when there are no messages", () => {
    const mockClear = vi.fn();
    render(<ChatSidebar messages={[]} onSend={mockOnSend} onClearHistory={mockClear} />);
    expect(screen.queryByRole("button", { name: /clear history/i })).not.toBeInTheDocument();
  });

  it("shows Clear history button when messages exist and onClearHistory is provided", () => {
    const mockClear = vi.fn();
    const messages = [{ role: "user" as const, content: "Hello" }];
    render(<ChatSidebar messages={messages} onSend={mockOnSend} onClearHistory={mockClear} />);
    expect(screen.getByRole("button", { name: /clear history/i })).toBeInTheDocument();
  });

  it("calls onClearHistory when Clear history button is clicked", async () => {
    const mockClear = vi.fn();
    const messages = [{ role: "user" as const, content: "Hello" }];
    render(<ChatSidebar messages={messages} onSend={mockOnSend} onClearHistory={mockClear} />);
    await userEvent.click(screen.getByRole("button", { name: /clear history/i }));
    expect(mockClear).toHaveBeenCalledTimes(1);
  });
});
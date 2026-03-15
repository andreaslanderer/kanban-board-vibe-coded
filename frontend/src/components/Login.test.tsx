import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { Login } from "@/components/Login";

const mockLoginWithGoogle = vi.fn();

vi.mock("@/lib/auth", () => ({
  useAuth: () => ({
    user: null,
    loading: false,
    loginWithGoogle: mockLoginWithGoogle,
    logout: vi.fn(),
  }),
}));

describe("Login", () => {
  beforeEach(() => {
    mockLoginWithGoogle.mockClear();
    // Reset search params to empty
    Object.defineProperty(window, "location", {
      value: { ...window.location, search: "" },
      writable: true,
    });
  });

  it("renders Sign in with Google button", () => {
    render(<Login />);
    expect(
      screen.getByRole("button", { name: /sign in with google/i })
    ).toBeInTheDocument();
  });

  it("renders Sign In heading", () => {
    render(<Login />);
    expect(screen.getByRole("heading", { name: /sign in/i })).toBeInTheDocument();
  });

  it("calls loginWithGoogle when button is clicked", async () => {
    render(<Login />);
    await userEvent.click(
      screen.getByRole("button", { name: /sign in with google/i })
    );
    expect(mockLoginWithGoogle).toHaveBeenCalledTimes(1);
  });

  it("shows OAuth error when ?error=oauth_failed is in URL", () => {
    Object.defineProperty(window, "location", {
      value: { ...window.location, search: "?error=oauth_failed" },
      writable: true,
    });
    render(<Login />);
    expect(screen.getByRole("alert")).toHaveTextContent(/sign in failed/i);
  });

  it("does not show error when no error param", () => {
    render(<Login />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { AuthProvider, useAuth } from "@/lib/auth";

vi.mock("@/lib/api", () => ({
  api: {
    getMe: vi.fn(),
    logout: vi.fn(),
  },
}));

import { api } from "@/lib/api";
const mockApi = vi.mocked(api);

/** Minimal consumer component that surfaces auth context values for assertions. */
function AuthConsumer() {
  const { user, loading, loginWithGoogle, logout } = useAuth();
  return (
    <div>
      <span data-testid="loading">{loading ? "loading" : "ready"}</span>
      <span data-testid="user">{user ? user.email : "none"}</span>
      <button onClick={loginWithGoogle}>Login with Google</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts in loading state then shows authenticated user", async () => {
    mockApi.getMe.mockResolvedValueOnce({
      id: 1,
      email: "test@example.com",
      display_name: "Test User",
      avatar_url: null,
    });

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    expect(screen.getByTestId("loading")).toHaveTextContent("loading");

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("ready")
    );
    expect(screen.getByTestId("user")).toHaveTextContent("test@example.com");
  });

  it("sets user to null when getMe returns null (unauthenticated)", async () => {
    mockApi.getMe.mockResolvedValueOnce(null);

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("ready")
    );
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });

  it("sets user to null when getMe throws (network error)", async () => {
    mockApi.getMe.mockRejectedValueOnce(new Error("Network error"));

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("ready")
    );
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });

  it("loginWithGoogle sets window.location.href to /api/auth/google", async () => {
    mockApi.getMe.mockResolvedValueOnce(null);

    Object.defineProperty(window, "location", {
      value: { href: "" },
      writable: true,
    });

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() =>
      expect(screen.getByTestId("loading")).toHaveTextContent("ready")
    );

    await userEvent.click(screen.getByRole("button", { name: /login with google/i }));
    expect(window.location.href).toBe("/api/auth/google");
  });

  it("logout calls api.logout and clears the user", async () => {
    mockApi.getMe.mockResolvedValueOnce({
      id: 1,
      email: "test@example.com",
      display_name: null,
      avatar_url: null,
    });
    mockApi.logout.mockResolvedValueOnce(undefined);

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    );

    await waitFor(() =>
      expect(screen.getByTestId("user")).toHaveTextContent("test@example.com")
    );

    await userEvent.click(screen.getByRole("button", { name: /logout/i }));

    expect(mockApi.logout).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });
});

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Login } from "@/components/Login";
import { AuthProvider } from "@/lib/auth";

describe("Login", () => {
  it("shows error on invalid credentials", async () => {
    render(
      <AuthProvider>
        <Login />
      </AuthProvider>
    );

    await userEvent.type(screen.getByLabelText(/username/i), "foo");
    await userEvent.type(screen.getByLabelText(/password/i), "bar");
    await userEvent.click(screen.getByRole("button", { name: /log in/i }));

    expect(screen.getByRole("alert")).toHaveTextContent("Invalid credentials");
  });

  it("calls login and clears error on valid credentials", async () => {
    render(
      <AuthProvider>
        <Login />
      </AuthProvider>
    );

    await userEvent.type(screen.getByLabelText(/username/i), "user");
    await userEvent.type(screen.getByLabelText(/password/i), "password");
    await userEvent.click(screen.getByRole("button", { name: /log in/i }));

    // error should no longer be present and inputs should be cleared
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByLabelText(/username/i)).toHaveValue("");
    expect(screen.getByLabelText(/password/i)).toHaveValue("");
  });
});

"use client";

import { useState, FormEvent } from "react";
import { useAuth } from "@/lib/auth";

export const Login = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const ok = login(username, password);
    if (!ok) {
      setError("Invalid credentials");
    } else {
      setError("");
      setUsername("");
      setPassword("");
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-6 rounded-lg border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]"
      >
        <h2 className="text-2xl font-semibold text-[var(--navy-dark)]">
          Sign In
        </h2>
        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
        <div>
          <label className="block text-sm font-medium text-[var(--navy-dark)]">
            Username
            <input
              name="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 w-full rounded border px-3 py-2"
              required
            />
          </label>
        </div>
        <div>
          <label className="block text-sm font-medium text-[var(--navy-dark)]">
            Password
            <input
              name="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded border px-3 py-2"
              required
            />
          </label>
        </div>
        <button
          type="submit"
          className="w-full rounded bg-[var(--primary-blue)] px-4 py-2 text-white"
        >
          Log in
        </button>
      </form>
    </div>
  );
};

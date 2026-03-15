"use client";

import { useAuth } from "@/lib/auth";

export const Login = () => {
  const { loginWithGoogle } = useAuth();

  const oauthError =
    typeof window !== "undefined" &&
    new URLSearchParams(window.location.search).get("error") === "oauth_failed";

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm space-y-6 rounded-lg border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
        <h2 className="text-2xl font-semibold text-[var(--navy-dark)]">
          Sign In
        </h2>
        {oauthError && (
          <p className="text-sm text-red-600" role="alert">
            Sign in failed. Please try again.
          </p>
        )}
        <button
          onClick={loginWithGoogle}
          className="w-full rounded bg-[var(--primary-blue)] px-4 py-2 text-white"
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
};

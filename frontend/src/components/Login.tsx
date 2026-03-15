"use client";

import { useAuth } from "@/lib/auth";

export const Login = () => {
  const { loginWithGoogle } = useAuth();

  const oauthError =
    typeof window !== "undefined" &&
    new URLSearchParams(window.location.search).get("error") === "oauth_failed";

  return (
    <div className="flex h-screen w-full">
      {/* Left panel — brand */}
      <div
        className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12"
        style={{ background: "var(--navy-dark)" }}
      >
        <span className="font-display text-xl font-bold text-white tracking-tight">
          Kanban Studio
        </span>

        <div className="space-y-4">
          <h1
            className="font-display text-5xl font-bold leading-tight text-white"
          >
            Your focused,<br />AI-powered<br />workspace.
          </h1>
          <p className="text-base" style={{ color: "rgba(255,255,255,0.55)" }}>
            Plan, track, and ship — with an AI that knows your board.
          </p>
        </div>

        {/* Decorative abstract Kanban columns */}
        <div className="flex items-end gap-4">
          {/* Column 1 — yellow */}
          <div className="flex flex-col gap-2 w-14">
            <div className="h-3 rounded" style={{ background: "var(--accent-yellow)" }} />
            <div className="h-3 rounded" style={{ background: "var(--accent-yellow)", opacity: 0.55 }} />
            <div className="h-3 w-3/4 rounded" style={{ background: "var(--accent-yellow)", opacity: 0.3 }} />
          </div>
          {/* Column 2 — blue */}
          <div className="flex flex-col gap-2 w-14">
            <div className="h-3 rounded" style={{ background: "var(--primary-blue)" }} />
            <div className="h-3 rounded" style={{ background: "var(--primary-blue)", opacity: 0.55 }} />
            <div className="h-3 rounded" style={{ background: "var(--primary-blue)", opacity: 0.3 }} />
            <div className="h-3 w-1/2 rounded" style={{ background: "var(--primary-blue)", opacity: 0.15 }} />
          </div>
          {/* Column 3 — purple */}
          <div className="flex flex-col gap-2 w-14">
            <div className="h-3 rounded" style={{ background: "var(--secondary-purple)" }} />
            <div className="h-3 w-3/4 rounded" style={{ background: "var(--secondary-purple)", opacity: 0.55 }} />
          </div>
          {/* Column 4 — muted */}
          <div className="flex flex-col gap-2 w-14">
            <div className="h-3 rounded" style={{ background: "rgba(255,255,255,0.2)" }} />
            <div className="h-3 w-1/2 rounded" style={{ background: "rgba(255,255,255,0.12)" }} />
          </div>
        </div>
      </div>

      {/* Right panel — sign in form */}
      <div
        className="flex flex-1 items-center justify-center p-8"
        style={{ background: "var(--surface)" }}
      >
        <div className="w-full max-w-sm space-y-8">
          {/* Mobile-only logo */}
          <div className="lg:hidden">
            <span
              className="font-display text-2xl font-bold"
              style={{ color: "var(--navy-dark)" }}
            >
              Kanban Studio
            </span>
          </div>

          <div className="space-y-2">
            <h2
              className="font-display text-3xl font-bold"
              style={{ color: "var(--navy-dark)" }}
            >
              Sign In
            </h2>
            <p className="text-sm" style={{ color: "var(--gray-text)" }}>
              Sign in to continue to your board.
            </p>
          </div>

          {oauthError && (
            <div
              role="alert"
              className="rounded-md border px-4 py-3 text-sm"
              style={{
                background: "#fef2f2",
                borderColor: "#fecaca",
                color: "#b91c1c",
              }}
            >
              Sign in failed. Please try again.
            </div>
          )}

          <button
            onClick={loginWithGoogle}
            className="flex w-full items-center justify-center gap-3 rounded-lg border px-4 py-3 text-sm font-medium transition-all hover:shadow-md active:scale-[0.98]"
            style={{
              background: "white",
              borderColor: "var(--stroke)",
              color: "var(--navy-dark)",
              boxShadow: "0 1px 3px rgba(3,33,71,0.08)",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
              <path
                d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
                fill="#4285F4"
              />
              <path
                d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"
                fill="#34A853"
              />
              <path
                d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"
                fill="#FBBC05"
              />
              <path
                d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"
                fill="#EA4335"
              />
            </svg>
            Sign in with Google
          </button>
        </div>
      </div>
    </div>
  );
};

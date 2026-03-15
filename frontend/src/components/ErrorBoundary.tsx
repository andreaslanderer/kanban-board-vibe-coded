"use client";

import { Component, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="max-w-md text-center">
            <h2 className="text-xl font-semibold text-[var(--navy-dark)]">Something went wrong</h2>
            <p className="mt-2 text-sm text-[var(--gray-text)]">{this.state.error.message}</p>
            <button
              className="mt-4 rounded-xl bg-[var(--primary-blue)] px-4 py-2 text-sm font-semibold text-white"
              onClick={() => this.setState({ error: null })}
            >
              Try again
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

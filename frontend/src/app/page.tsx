"use client";

import { KanbanBoard } from "@/components/KanbanBoard";
import { useAuth } from "@/lib/auth";
import { Login } from "@/components/Login";

export default function Home() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Login />;
  return <KanbanBoard />;
}

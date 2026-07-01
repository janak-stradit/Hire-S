"use client";
import { AppShell } from "../../src/components/AppShell";
export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}

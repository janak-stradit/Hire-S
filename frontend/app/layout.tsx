import type { Metadata } from "next";
import "../src/styles/index.css";

export const metadata: Metadata = {
  title: "HireX — Talent Operations Platform",
  description: "Enterprise candidate intelligence and hiring automation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

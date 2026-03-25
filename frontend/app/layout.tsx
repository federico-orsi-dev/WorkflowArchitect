import type { ReactNode } from "react";
import "./globals.css";
import { Toaster } from "sonner";

export const metadata = {
  title: "WorkflowArchitect",
  description: "Planning and commit assistance for fast-moving teams.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        {children}
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
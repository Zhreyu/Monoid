import type { Metadata } from "next";
import { Suspense } from "react";
import SPARedirect from "@/components/SPARedirect";
import "./globals.css";

export const metadata: Metadata = {
  title: "monoid",
  description: "Your thoughts, structured beautifully",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Suspense fallback={null}>
          <SPARedirect />
        </Suspense>
        <div className="min-h-screen bg-[var(--color-bg)]">
          {children}
        </div>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
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
        <div className="min-h-screen bg-[var(--color-bg)]">
          {children}
        </div>
      </body>
    </html>
  );
}

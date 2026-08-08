import type { Metadata } from "next";
import { Inter, Fira_Code } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const firaCode = Fira_Code({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CyberGhost OSINT Enterprise",
  description: "Enterprise Cyber Threat Intelligence Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${firaCode.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-[var(--color-cyber-dark)] text-[var(--color-cyber-text)]">
        {children}
      </body>
    </html>
  );
}

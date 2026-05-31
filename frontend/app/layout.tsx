import type { Metadata } from "next";
import { Fraunces, JetBrains_Mono, Geist } from "next/font/google";
import "./globals.css";

const display = Fraunces({ subsets: ["latin"], variable: "--ff-display", display: "swap" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--ff-mono", display: "swap" });
const sans = Geist({ subsets: ["latin"], variable: "--ff-sans", display: "swap" });

export const metadata: Metadata = {
  title: "SuperNinja — prompt to deployed app",
  description:
    "Describe an app. SuperNinja generates it with Claude, pushes it to GitHub, and deploys it to Vercel.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${mono.variable} ${sans.variable} antialiased`}
    >
      <body>{children}</body>
    </html>
  );
}

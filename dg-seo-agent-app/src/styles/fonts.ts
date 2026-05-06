import { Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";

export const fontSans = Plus_Jakarta_Sans({
  variable: "--font-sans-loaded",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
});

export const fontMono = JetBrains_Mono({
  variable: "--font-mono-loaded",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const fontVariables = `${fontSans.variable} ${fontMono.variable}`;

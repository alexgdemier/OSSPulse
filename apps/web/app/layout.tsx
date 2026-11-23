import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OSS Pulse — Open Source Maintenance Intelligence",
  description: "Understand the health of your open source project and discover what needs attention.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

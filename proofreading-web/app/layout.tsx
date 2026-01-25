import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ProofsLab - PDF Comparison Tool",
  description: "Compare printed materials against original designs using AI-powered similarity analysis. The PDF comparison laboratory for print professionals.",
  keywords: ["PDF comparison", "print proofing", "SSIM", "document comparison", "quality control"],
  authors: [{ name: "ProofsLab" }],
  icons: {
    icon: "/favicon.ico",
    apple: "/logo.png",
  },
  openGraph: {
    title: "ProofsLab - PDF Comparison Tool",
    description: "Compare printed materials against original designs using AI-powered similarity analysis.",
    url: "https://proofslab.com",
    siteName: "ProofsLab",
    type: "website",
    images: [
      {
        url: "/logo.png",
        width: 512,
        height: 512,
        alt: "ProofsLab Logo",
      },
    ],
  },
  twitter: {
    card: "summary",
    title: "ProofsLab - PDF Comparison Tool",
    description: "Compare printed materials against original designs using AI-powered similarity analysis.",
    images: ["/logo.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen bg-background`}
      >
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}

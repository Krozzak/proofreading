import type { Metadata } from "next";
import { Geist, Geist_Mono, Instrument_Serif } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { CookieBanner } from "@/components/CookieBanner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument-serif",
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Proofslab — Approuvez vos PDF à la vitesse du pixel",
  description: "Comparez vos fichiers design aux épreuves imprimeur pixel par pixel. Score SSIM, heatmap des écarts, approbation en un clic.",
  keywords: ["PDF comparison", "PDF", "print proofing", "SSIM", "document comparison", "quality control"],
  authors: [{ name: "Proofslab" }],
  icons: {
    icon: "/logo.svg",
    apple: "/logo-apple.png",
  },
  openGraph: {
    title: "Proofslab — Approuvez vos PDF à la vitesse du pixel",
    description: "Comparez vos fichiers design aux épreuves imprimeur pixel par pixel. Score SSIM, heatmap, approbation batch.",
    url: "https://proofslab.com",
    siteName: "Proofslab",
    type: "website",
    images: [
      {
        url: "/logo.png",
        width: 512,
        height: 512,
        alt: "Proofslab Logo",
      },
    ],
  },
  twitter: {
    card: "summary",
    title: "Proofslab — Approuvez vos PDF à la vitesse du pixel",
    description: "Comparez vos fichiers design aux épreuves imprimeur pixel par pixel.",
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
        className={`${geistSans.variable} ${geistMono.variable} ${instrumentSerif.variable} antialiased min-h-screen bg-background`}
      >
        <AuthProvider>
          {children}
          <CookieBanner />
        </AuthProvider>
      </body>
    </html>
  );
}

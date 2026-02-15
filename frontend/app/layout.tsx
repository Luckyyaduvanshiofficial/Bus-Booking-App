import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "next-themes";
import { Providers } from "@/lib/providers";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  display: "swap",
  subsets: ["latin"],
});

const defaultUrl = process.env.VERCEL_URL
  ? `https://${process.env.VERCEL_URL}`
  : "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(defaultUrl),
  title: {
    default: "BusBook — Book Buses for Group Travel in Rajasthan",
    template: "%s | BusBook",
  },
  description:
    "Book mini buses, tempo travellers, and luxury coaches for weddings, family trips, and group travel across Rajasthan. Verified operators, secure payments, best prices.",
  keywords: [
    "bus booking",
    "bus hire Rajasthan",
    "tempo traveller Jaipur",
    "group travel",
    "wedding bus",
    "charter bus",
    "mini bus rental",
  ],
  openGraph: {
    title: "BusBook — Rajasthan's Trusted Bus Booking Platform",
    description:
      "Book verified buses for group travel. Weddings, family trips, pilgrimages. Best prices in Rajasthan.",
    siteName: "BusBook",
    type: "website",
    locale: "en_IN",
  },
  twitter: {
    card: "summary_large_image",
    title: "BusBook — Book Buses for Group Travel",
    description:
      "Verified operators, secure payments, best prices across Rajasthan.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem={false}
          disableTransitionOnChange
        >
          <Providers>{children}</Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}

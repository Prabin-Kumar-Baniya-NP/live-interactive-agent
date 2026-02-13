import { inter, outfit } from '@/styles/fonts';
import '@/styles/globals.css';
import type { Viewport, Metadata } from 'next';
import { ThemeProvider } from '@/hooks/useTheme';

export const metadata: Metadata = {
  title: {
    default: 'Live Interactive Agent',
    template: '%s | Live Interactive Agent',
  },
  description: 'AI Agent Platform with real-time voice, video, and tools.',
  icons: {
    icon: '/favicon.ico',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${outfit.variable}`}>
      <body>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/context/auth-context';
import { WebSocketProvider } from '@/context/websocket-context';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'KisanSetu AI — Smart Procurement Management',
  description:
    'Smart Procurement. Smart Queues. Empowered Farmers. | SIH Problem Statement 26032 | Department of Consumer Affairs',
  keywords: ['KisanSetu', 'Smart India Hackathon', 'Farmer', 'Procurement', 'Mandi', 'DoCA'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`${inter.className} font-sans antialiased text-slate-900 bg-slate-50 min-h-screen`}>
        <AuthProvider>
          <WebSocketProvider>
            {children}
          </WebSocketProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

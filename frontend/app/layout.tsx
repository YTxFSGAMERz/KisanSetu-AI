import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/context/auth-context';
import { WebSocketProvider } from '@/context/websocket-context';

const inter = Inter({ subsets: ['latin'] });

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
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>
          <WebSocketProvider>
            {children}
          </WebSocketProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

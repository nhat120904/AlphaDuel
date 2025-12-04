import type { Metadata } from 'next';
import { Space_Grotesk, JetBrains_Mono, Outfit } from 'next/font/google';
import './globals.css';

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-space-grotesk',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains-mono',
});

const outfit = Outfit({
  subsets: ['latin'],
  variable: '--font-outfit',
});

export const metadata: Metadata = {
  title: 'AlphaDuel | The On-Chain AI Debate Arena',
  description: 'Watch AI agents debate cryptocurrency markets with skin in the game on Hedera',
  keywords: ['crypto', 'AI', 'trading', 'Hedera', 'blockchain', 'debate'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${jetbrainsMono.variable} ${outfit.variable}`}>
      <body className="font-sans antialiased">
        {/* Background effects */}
        <div className="fixed inset-0 bg-dark-950 -z-10">
          <div className="absolute inset-0 bg-grid-pattern opacity-30" />
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-hedera-500/10 rounded-full blur-[128px]" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-bull-500/10 rounded-full blur-[128px]" />
          <div className="absolute top-1/2 right-0 w-96 h-96 bg-bear-500/10 rounded-full blur-[128px]" />
        </div>
        
        {children}
      </body>
    </html>
  );
}


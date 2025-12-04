'use client';

import { Header, DebateArena, ChatInput } from '@/components';
import { useDebate } from '@/hooks/useDebate';

export default function Home() {
  const { messages, status, startDebate, reset, isLoading, currentAgent } = useDebate();

  const handleSubmit = (query: string, symbol: string) => {
    startDebate(query, symbol);
  };

  const isDebating = status === 'debating' || status === 'loading';

  return (
    <div className="flex flex-col min-h-screen">
      <Header onReset={reset} isDebating={isDebating} />
      
      <main className="flex-1 flex flex-col max-w-5xl mx-auto w-full">
        <DebateArena 
          messages={messages} 
          isLoading={isLoading}
          currentAgent={currentAgent ?? undefined}
        />
        
        <ChatInput 
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}


'use client';

import { useState, useEffect } from 'react';
import { Header, DebateArena, ChatInput } from '@/components';
import { useDebate } from '@/hooks/useDebate';
import type { AgentMessage } from '@/types';

export default function Home() {
  const { messages, status, startDebate, reset, isLoading } = useDebate();
  const [currentAgent, setCurrentAgent] = useState<string | undefined>();

  // Track which agent is currently "speaking"
  useEffect(() => {
    if (status === 'debating') {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage?.node) {
        if (lastMessage.node.includes('bull')) {
          setCurrentAgent('bull');
        } else if (lastMessage.node.includes('bear')) {
          setCurrentAgent('bear');
        } else if (lastMessage.node.includes('referee')) {
          setCurrentAgent('referee');
        }
      }
    } else {
      setCurrentAgent(undefined);
    }
  }, [messages, status]);

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
          currentAgent={currentAgent}
        />
        
        <ChatInput 
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}


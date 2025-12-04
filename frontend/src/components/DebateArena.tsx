'use client';

import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scale } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { BullBubble } from './BullBubble';
import { BearBubble } from './BearBubble';
import { RefereeCard } from './RefereeCard';
import { SystemMessage } from './SystemMessage';
import type { AgentMessage } from '@/types';

interface DebateArenaProps {
  messages: AgentMessage[];
  isLoading: boolean;
  currentAgent?: string;
}

export function DebateArena({ messages, isLoading, currentAgent }: DebateArenaProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const renderMessage = (message: AgentMessage, index: number) => {
    switch (message.type) {
      case 'bull':
        return (
          <BullBubble
            key={index}
            content={message.content || ''}
            confidence={message.confidence}
            keyPoints={message.key_points}
            round={message.round}
          />
        );
      
      case 'bear':
        return (
          <BearBubble
            key={index}
            content={message.content || ''}
            confidence={message.confidence}
            keyPoints={message.key_points}
            round={message.round}
          />
        );
      
      case 'referee':
        // Skip rendering if there's a hedera message (it will render the complete card with transactions)
        const hasHederaMessage = messages.some(m => m.type === 'hedera');
        if (hasHederaMessage) {
          return null;
        }
        // If no winner yet, this is streaming content - show it in a simpler format
        if (!message.winner) {
          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-full max-w-2xl mx-auto"
            >
              <div className="glass-hedera rounded-2xl p-6 glow-hedera">
                <div className="flex items-center gap-3 mb-4">
                  <Scale className="w-6 h-6 text-hedera-400" />
                  <span className="text-hedera-300 font-medium">Referee is deliberating...</span>
                </div>
                <div className="prose prose-invert prose-sm max-w-none prose-p:text-dark-200">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content || ''}
                  </ReactMarkdown>
                </div>
              </div>
            </motion.div>
          );
        }
        return (
          <RefereeCard
            key={index}
            winner={message.winner}
            confidenceScore={message.confidence_score || 50}
            wagerAmount={message.wager_amount || 0}
            reasoning={message.content || ''}
            keyFactors={message.key_factors}
          />
        );
      
      case 'hedera':
        const refereeMessage = messages.find(m => m.type === 'referee');
        return (
          <RefereeCard
            key={index}
            winner={refereeMessage?.winner || 'Bull'}
            confidenceScore={refereeMessage?.confidence_score || 50}
            wagerAmount={refereeMessage?.wager_amount || 0}
            reasoning={refereeMessage?.content || ''}
            keyFactors={refereeMessage?.key_factors}
            hcsTx={message.hcs_tx}
            wagerTx={message.wager_tx}
          />
        );
      
      case 'system':
        return (
          <SystemMessage
            key={index}
            content={message.content || ''}
            data={message.data}
          />
        );
      
      case 'error':
        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-auto max-w-md p-4 rounded-xl bg-bear-900/30 border border-bear-700/50 text-bear-300 text-center"
          >
            ⚠️ {message.content}
          </motion.div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto p-6 space-y-6"
    >
      <AnimatePresence mode="popLayout">
        {messages.map((message, index) => renderMessage(message, index))}
        
        {/* Loading indicators - only show if no streaming content yet */}
        {isLoading && currentAgent === 'bull' && !messages.some(m => m.type === 'bull' && !m.confidence) && (
          <BullBubble key="loading-bull" content="" isLoading />
        )}
        {isLoading && currentAgent === 'bear' && !messages.some(m => m.type === 'bear' && !m.confidence) && (
          <BearBubble key="loading-bear" content="" isLoading />
        )}
        {isLoading && currentAgent === 'referee' && !messages.some(m => m.type === 'referee' && !m.winner) && (
          <RefereeCard
            key="loading-referee"
            winner="Bull"
            confidenceScore={0}
            wagerAmount={0}
            reasoning=""
            isLoading
          />
        )}
      </AnimatePresence>

      {messages.length === 0 && !isLoading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center h-full text-center py-20"
        >
          <div className="text-6xl mb-6">🐂 ⚔️ 🐻</div>
          <h2 className="text-2xl font-display font-bold text-dark-200 mb-2">
            Ready for Battle
          </h2>
          <p className="text-dark-400 max-w-md">
            Ask about any cryptocurrency and watch our AI agents debate the market outlook
            with real stakes on Hedera.
          </p>
        </motion.div>
      )}
    </div>
  );
}


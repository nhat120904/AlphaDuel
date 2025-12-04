'use client';

import { motion } from 'framer-motion';
import { TrendingDown, AlertTriangle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';

// Helper to strip markdown syntax for display in tags
function stripMarkdown(text: string): string {
  return text
    .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold **text**
    .replace(/\*([^*]+)\*/g, '$1')     // Remove italic *text*
    .replace(/__([^_]+)__/g, '$1')     // Remove bold __text__
    .replace(/_([^_]+)_/g, '$1')       // Remove italic _text_
    .replace(/`([^`]+)`/g, '$1')       // Remove code `text`
    .replace(/#+\s?/g, '')             // Remove headers
    .trim();
}

interface BearBubbleProps {
  content: string;
  confidence?: number;
  keyPoints?: string[];
  round?: number;
  isLoading?: boolean;
}

export function BearBubble({ 
  content, 
  confidence, 
  keyPoints, 
  round,
  isLoading 
}: BearBubbleProps) {
  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex items-start gap-3 max-w-[85%] ml-auto flex-row-reverse"
      >
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-bear-600 flex items-center justify-center">
          <span className="text-lg">🐻</span>
        </div>
        <div className="glass-bear rounded-2xl rounded-tr-sm p-4 glow-bear">
          <div className="typing-indicator">
            <span className="bg-bear-400" />
            <span className="bg-bear-400" />
            <span className="bg-bear-400" />
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="flex items-start gap-3 max-w-[85%] ml-auto flex-row-reverse"
    >
      {/* Avatar */}
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-bear-500 to-bear-700 flex items-center justify-center shadow-lg shadow-bear-500/30">
        <span className="text-lg">🐻</span>
      </div>

      {/* Message bubble */}
      <div className="flex flex-col gap-2 items-end">
        {/* Header */}
        <div className="flex items-center gap-2 text-sm">
          {confidence !== undefined && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-bear-900/50 text-bear-300 text-xs">
              <AlertTriangle className="w-3 h-3" />
              {confidence}% confident
            </span>
          )}
          {round && (
            <span className="px-2 py-0.5 rounded-full bg-bear-900/50 text-bear-300 text-xs">
              Round {round}
            </span>
          )}
          <span className="font-semibold text-bear-400">Bear Agent</span>
        </div>

        {/* Main content */}
        <div className={cn(
          "glass-bear rounded-2xl rounded-tr-sm p-4 glow-bear",
          "border-r-4 border-bear-500"
        )}>
          <div className="prose prose-invert prose-sm max-w-none prose-headings:text-bear-300 prose-strong:text-bear-200 prose-li:text-dark-100 prose-p:text-dark-100 prose-ul:my-2 prose-li:my-0.5">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {content}
            </ReactMarkdown>
          </div>
        </div>

        {/* Key points */}
        {keyPoints && keyPoints.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-wrap gap-2 mt-1 justify-end"
          >
            {keyPoints.slice(0, 3).map((point, idx) => {
              const cleanPoint = stripMarkdown(point);
              return (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-bear-900/30 text-bear-300 text-xs"
                >
                  <TrendingDown className="w-3 h-3" />
                  {cleanPoint.slice(0, 50)}{cleanPoint.length > 50 ? '...' : ''}
                </span>
              );
            })}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}


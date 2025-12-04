'use client';

import { useState, FormEvent } from 'react';
import { motion } from 'framer-motion';
import { Send, Loader2, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';

const SYMBOLS = [
  { symbol: 'HBAR', name: 'Hedera' },
  { symbol: 'BTC', name: 'Bitcoin' },
  { symbol: 'ETH', name: 'Ethereum' },
  { symbol: 'SOL', name: 'Solana' },
  { symbol: 'AVAX', name: 'Avalanche' },
];

interface ChatInputProps {
  onSubmit: (query: string, symbol: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSubmit, isLoading, disabled }: ChatInputProps) {
  const [query, setQuery] = useState('');
  const [symbol, setSymbol] = useState('HBAR');
  const [showSymbols, setShowSymbols] = useState(false);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading && !disabled) {
      onSubmit(query.trim(), symbol);
      setQuery('');
    }
  };

  const selectedSymbol = SYMBOLS.find(s => s.symbol === symbol);

  return (
    <div className="border-t border-dark-800 bg-dark-900/80 backdrop-blur-xl p-4">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="flex gap-3 items-center">
          {/* Symbol selector */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowSymbols(!showSymbols)}
              className={cn(
                "flex items-center gap-2 px-4 h-12 rounded-xl",
                "bg-dark-800 border border-dark-700",
                "hover:border-hedera-500/50 transition-colors",
                "text-sm font-medium"
              )}
            >
              <span className="text-hedera-400">{selectedSymbol?.symbol}</span>
              <ChevronDown className={cn(
                "w-4 h-4 text-dark-400 transition-transform",
                showSymbols && "rotate-180"
              )} />
            </button>
            
            {showSymbols && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute bottom-full mb-2 left-0 w-48 py-2 rounded-xl bg-dark-800 border border-dark-700 shadow-xl z-10"
              >
                {SYMBOLS.map((s) => (
                  <button
                    key={s.symbol}
                    type="button"
                    onClick={() => {
                      setSymbol(s.symbol);
                      setShowSymbols(false);
                    }}
                    className={cn(
                      "w-full px-4 py-2 text-left text-sm flex items-center justify-between",
                      "hover:bg-dark-700/50 transition-colors",
                      symbol === s.symbol && "bg-hedera-900/30 text-hedera-400"
                    )}
                  >
                    <span>{s.name}</span>
                    <span className="text-dark-500 font-mono">{s.symbol}</span>
                  </button>
                ))}
              </motion.div>
            )}
          </div>

          {/* Input field */}
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder={`Ask about ${symbol} market outlook...`}
              disabled={isLoading || disabled}
              className={cn(
                "w-full px-4 h-12 rounded-xl",
                "bg-dark-800 border border-dark-700",
                "focus:outline-none focus:ring-2 focus:ring-hedera-500/50 focus:border-hedera-500",
                "placeholder:text-dark-500",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "transition-all duration-200"
              )}
            />
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={!query.trim() || isLoading || disabled}
            className={cn(
              "flex items-center justify-center w-12 h-12 rounded-xl",
              "bg-gradient-to-r from-hedera-600 to-hedera-500",
              "hover:from-hedera-500 hover:to-hedera-400",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-all duration-200",
              "active:scale-95"
            )}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 text-white animate-spin" />
            ) : (
              <Send className="w-5 h-5 text-white" />
            )}
          </button>
        </div>

        {/* Quick prompts */}
        <div className="flex flex-wrap gap-2 mt-3">
          {[
            `What's the outlook for ${symbol} today?`,
            `Is ${symbol} a good buy right now?`,
            `Will ${symbol} go up or down this week?`,
          ].map((prompt, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setQuery(prompt)}
              disabled={isLoading}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs",
                "bg-dark-800/50 border border-dark-700/50",
                "hover:border-hedera-500/30 hover:text-hedera-400",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "transition-colors"
              )}
            >
              {prompt}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}


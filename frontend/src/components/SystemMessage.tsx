'use client';

import { motion } from 'framer-motion';
import { Info, BarChart3 } from 'lucide-react';
import { formatPrice, formatPercentage } from '@/lib/utils';

interface SystemMessageProps {
  content: string;
  data?: Record<string, unknown>;
}

export function SystemMessage({ content, data }: SystemMessageProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-center"
    >
      <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-dark-800/50 border border-dark-700/50">
        <Info className="w-4 h-4 text-hedera-400" />
        <span className="text-sm text-dark-300">{content}</span>
        
        {data && (
          <div className="flex items-center gap-2 pl-2 border-l border-dark-700">
            {data.price !== undefined && (
              <span className="flex items-center gap-1 text-sm font-mono text-dark-200">
                <BarChart3 className="w-3 h-3 text-hedera-400" />
                {formatPrice(data.price as number)}
              </span>
            )}
            {data.change_24h !== undefined && (
              <span className={`text-sm font-mono ${
                (data.change_24h as number) >= 0 ? 'text-bull-400' : 'text-bear-400'
              }`}>
                {formatPercentage(data.change_24h as number)}
              </span>
            )}
            {data.rsi !== undefined && (
              <span className="text-sm font-mono text-dark-400">
                RSI: {(data.rsi as number).toFixed(1)}
              </span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}


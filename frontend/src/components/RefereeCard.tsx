'use client';

import { motion } from 'framer-motion';
import { Scale, Trophy, ExternalLink, Coins, FileCheck } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';
import type { HederaTransaction } from '@/types';

interface RefereeCardProps {
  winner: 'Bull' | 'Bear';
  confidenceScore: number;
  wagerAmount: number;
  reasoning: string;
  keyFactors?: string[];
  hcsTx?: HederaTransaction;
  wagerTx?: HederaTransaction;
  isLoading?: boolean;
}

export function RefereeCard({
  winner,
  confidenceScore,
  wagerAmount,
  reasoning,
  keyFactors,
  hcsTx,
  wagerTx,
  isLoading,
}: RefereeCardProps) {
  const isBullWinner = winner === 'Bull';

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-2xl mx-auto"
      >
        <div className="glass-hedera rounded-2xl p-6 glow-hedera">
          <div className="flex items-center gap-3 mb-4">
            <Scale className="w-6 h-6 text-hedera-400 animate-pulse" />
            <span className="text-hedera-300 font-medium">Referee is evaluating...</span>
          </div>
          <div className="h-24 flex items-center justify-center">
            <div className="typing-indicator">
              <span className="bg-hedera-400" />
              <span className="bg-hedera-400" />
              <span className="bg-hedera-400" />
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 20 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="w-full max-w-2xl mx-auto"
    >
      <div className={cn(
        "rounded-2xl overflow-hidden",
        "bg-gradient-to-br from-dark-900 to-dark-800",
        "border-2",
        isBullWinner ? "border-bull-500/50" : "border-bear-500/50"
      )}>
        {/* Header */}
        <div className={cn(
          "p-4 flex items-center justify-between",
          "bg-gradient-to-r",
          isBullWinner 
            ? "from-bull-900/80 to-bull-800/50" 
            : "from-bear-900/80 to-bear-800/50"
        )}>
          <div className="flex items-center gap-3">
            <Scale className="w-6 h-6 text-hedera-400" />
            <span className="font-display font-bold text-lg text-white">Referee's Verdict</span>
          </div>
          <div className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-full",
            isBullWinner ? "bg-bull-500/20" : "bg-bear-500/20"
          )}>
            <Trophy className={cn("w-4 h-4", isBullWinner ? "text-bull-400" : "text-bear-400")} />
            <span className={cn("font-bold", isBullWinner ? "text-bull-400" : "text-bear-400")}>
              {winner} Wins!
            </span>
          </div>
        </div>

        {/* Stats */}
        <div className="p-4 grid grid-cols-2 gap-4 border-b border-dark-700/50">
          <div className="text-center p-3 rounded-xl bg-dark-800/50">
            <div className="text-sm text-dark-400 mb-1">Confidence Score</div>
            <div className={cn(
              "text-2xl font-bold font-mono",
              confidenceScore >= 70 ? "text-bull-400" : 
              confidenceScore >= 40 ? "text-yellow-400" : "text-bear-400"
            )}>
              {confidenceScore}%
            </div>
          </div>
          <div className="text-center p-3 rounded-xl bg-dark-800/50">
            <div className="text-sm text-dark-400 mb-1">Wager Amount</div>
            <div className="text-2xl font-bold font-mono text-hedera-400">
              {wagerAmount} HBAR
            </div>
          </div>
        </div>

        {/* Reasoning */}
        <div className="p-4 border-b border-dark-700/50">
          <h4 className="text-sm font-semibold text-dark-300 mb-2">Reasoning</h4>
          <div className="prose prose-invert prose-sm max-w-none prose-p:text-dark-200 prose-p:leading-relaxed prose-strong:text-hedera-300 prose-ul:my-2 prose-li:my-0.5 prose-li:text-dark-200">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {reasoning}
            </ReactMarkdown>
          </div>
        </div>

        {/* Key Factors */}
        {keyFactors && keyFactors.length > 0 && (
          <div className="p-4 border-b border-dark-700/50">
            <h4 className="text-sm font-semibold text-dark-300 mb-2">Key Factors</h4>
            <ul className="space-y-1">
              {keyFactors.map((factor, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-dark-300">
                  <span className={cn(
                    "w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold",
                    isBullWinner ? "bg-bull-900/50 text-bull-400" : "bg-bear-900/50 text-bear-400"
                  )}>
                    {idx + 1}
                  </span>
                  {factor}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Hedera Transactions */}
        <div className="p-4 bg-hedera-900/20">
          <h4 className="text-sm font-semibold text-hedera-300 mb-3 flex items-center gap-2">
            <FileCheck className="w-4 h-4" />
            On-Chain Proof (Hedera Testnet)
          </h4>
          <div className="space-y-2">
            {hcsTx && (
              <a
                href={hcsTx.hashscan_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 rounded-lg bg-dark-800/50 hover:bg-dark-700/50 transition-colors group"
              >
                <div className="flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-hedera-400" />
                  <span className="text-sm text-dark-300">HCS Log</span>
                  {hcsTx.simulation && (
                    <span className="px-1.5 py-0.5 text-xs rounded bg-yellow-900/30 text-yellow-400">
                      Simulation
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 text-hedera-400">
                  <code className="text-xs font-mono">
                    {hcsTx.tx_id.slice(0, 20)}...
                  </code>
                  <ExternalLink className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </a>
            )}
            {wagerTx && (
              <a
                href={wagerTx.hashscan_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 rounded-lg bg-dark-800/50 hover:bg-dark-700/50 transition-colors group"
              >
                <div className="flex items-center gap-2">
                  <Coins className="w-4 h-4 text-hedera-400" />
                  <span className="text-sm text-dark-300">Wager Transfer</span>
                  <span className="text-xs text-hedera-400 font-mono">
                    {wagerTx.amount} HBAR
                  </span>
                  {wagerTx.simulation && (
                    <span className="px-1.5 py-0.5 text-xs rounded bg-yellow-900/30 text-yellow-400">
                      Simulation
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 text-hedera-400">
                  <code className="text-xs font-mono">
                    {wagerTx.tx_id.slice(0, 20)}...
                  </code>
                  <ExternalLink className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </a>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}


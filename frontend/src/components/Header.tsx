'use client';

import { motion } from 'framer-motion';
import { Swords, Github, ExternalLink } from 'lucide-react';
import { cn } from '@/lib/utils';

interface HeaderProps {
  onReset?: () => void;
  isDebating?: boolean;
}

export function Header({ onReset, isDebating }: HeaderProps) {
  return (
    <header className="border-b border-dark-800 bg-dark-900/80 backdrop-blur-xl sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3"
        >
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-hedera-500 to-hedera-700 flex items-center justify-center shadow-lg shadow-hedera-500/30">
              <Swords className="w-5 h-5 text-white" />
            </div>
            <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-bull-500 border-2 border-dark-900 animate-pulse" />
          </div>
          <div>
            <h1 className="font-display font-bold text-xl text-white">
              Alpha<span className="text-hedera-400">Duel</span>
            </h1>
            <p className="text-xs text-dark-400 -mt-0.5">
              AI Debate Arena on Hedera
            </p>
          </div>
        </motion.div>

        {/* Center - Status */}
        {isDebating && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-dark-800/50 border border-dark-700"
          >
            <div className="w-2 h-2 rounded-full bg-bull-500 animate-pulse" />
            <span className="text-sm text-dark-300">Debate in progress...</span>
          </motion.div>
        )}

        {/* Right - Actions */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="flex items-center gap-3"
        >
          {onReset && isDebating && (
            <button
              onClick={onReset}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-dark-800 hover:bg-dark-700 border border-dark-700 transition-colors"
            >
              New Debate
            </button>
          )}
          
          <a
            href="https://hashscan.io/testnet"
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-lg text-sm",
              "bg-hedera-900/30 border border-hedera-700/30",
              "hover:bg-hedera-900/50 transition-colors",
              "text-hedera-400"
            )}
          >
            <span>HashScan</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </motion.div>
      </div>
    </header>
  );
}


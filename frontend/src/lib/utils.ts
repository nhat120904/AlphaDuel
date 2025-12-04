import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(num: number, decimals: number = 2): string {
  if (num >= 1_000_000_000) {
    return `$${(num / 1_000_000_000).toFixed(decimals)}B`;
  }
  if (num >= 1_000_000) {
    return `$${(num / 1_000_000).toFixed(decimals)}M`;
  }
  if (num >= 1_000) {
    return `$${(num / 1_000).toFixed(decimals)}K`;
  }
  return `$${num.toFixed(decimals)}`;
}

export function formatPrice(price: number): string {
  if (price < 0.01) {
    return `$${price.toFixed(6)}`;
  }
  if (price < 1) {
    return `$${price.toFixed(4)}`;
  }
  if (price < 100) {
    return `$${price.toFixed(2)}`;
  }
  return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatPercentage(pct: number): string {
  const sign = pct >= 0 ? '+' : '';
  return `${sign}${pct.toFixed(2)}%`;
}

export function truncateMiddle(str: string, startChars: number = 6, endChars: number = 4): string {
  if (str.length <= startChars + endChars) return str;
  return `${str.slice(0, startChars)}...${str.slice(-endChars)}`;
}


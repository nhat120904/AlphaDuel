export interface MarketData {
  symbol: string;
  current_price: number;
  price_change_24h: number;
  price_change_percentage_24h: number;
  market_cap: number;
  total_volume: number;
  high_24h: number;
  low_24h: number;
  rsi: number;
  news_summary: string;
  sentiment_score: number;
}

export interface AgentMessage {
  type: 'bull' | 'bear' | 'referee' | 'system' | 'hedera' | 'error' | 'status' | 'done' 
    | 'bull_token' | 'bear_token' | 'referee_token' 
    | 'bull_complete' | 'bear_complete' | 'referee_complete';
  content?: string;
  token?: string;
  confidence?: number;
  key_points?: string[];
  round?: number;
  winner?: 'Bull' | 'Bear';
  confidence_score?: number;
  wager_amount?: number;
  key_factors?: string[];
  hcs_tx?: HederaTransaction;
  wager_tx?: HederaTransaction;
  data?: Record<string, unknown>;
  node?: string;
  status?: string;
}

export interface HederaTransaction {
  tx_id: string;
  tx_type: 'HCS_LOG' | 'TRANSFER';
  status: string;
  hashscan_url: string;
  amount?: number;
  topic_id?: string;
  from_account?: string;
  to_account?: string;
  memo?: string;
  timestamp?: string;
  simulation?: boolean;
}

export interface DebateState {
  status: 'idle' | 'loading' | 'debating' | 'completed' | 'error';
  messages: AgentMessage[];
  symbol: string;
  query: string;
  winner?: 'Bull' | 'Bear';
  confidence_score?: number;
  wager_amount?: number;
  hcs_tx?: HederaTransaction;
  wager_tx?: HederaTransaction;
}

export interface Symbol {
  symbol: string;
  name: string;
  id: string;
}


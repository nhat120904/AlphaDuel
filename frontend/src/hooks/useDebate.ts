'use client';

import { useState, useCallback, useRef } from 'react';
import type { AgentMessage, DebateState, HederaTransaction } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useDebate() {
  const [state, setState] = useState<DebateState>({
    status: 'idle',
    messages: [],
    symbol: 'HBAR',
    query: '',
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const startDebate = useCallback(async (query: string, symbol: string = 'HBAR') => {
    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    setState({
      status: 'loading',
      messages: [],
      symbol,
      query,
    });

    try {
      const response = await fetch(`${API_URL}/api/debate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, symbol }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      setState(prev => ({ ...prev, status: 'debating' }));

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // Process complete SSE messages
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) as AgentMessage;
              
              // Update state based on message type
              setState(prev => {
                const newMessages = [...prev.messages, data];
                
                const updates: Partial<DebateState> = {
                  messages: newMessages,
                };

                if (data.type === 'done') {
                  updates.status = 'completed';
                } else if (data.type === 'error') {
                  updates.status = 'error';
                } else if (data.type === 'referee') {
                  updates.winner = data.winner;
                  updates.confidence_score = data.confidence_score;
                  updates.wager_amount = data.wager_amount;
                } else if (data.type === 'hedera') {
                  updates.hcs_tx = data.hcs_tx;
                  updates.wager_tx = data.wager_tx;
                }

                return { ...prev, ...updates };
              });
            } catch (e) {
              console.error('Failed to parse SSE message:', e);
            }
          }
        }
      }

      setState(prev => ({ ...prev, status: 'completed' }));
    } catch (error) {
      if ((error as Error).name === 'AbortError') {
        console.log('Request aborted');
        return;
      }
      
      console.error('Debate error:', error);
      setState(prev => ({
        ...prev,
        status: 'error',
        messages: [
          ...prev.messages,
          {
            type: 'error',
            content: (error as Error).message || 'An error occurred',
          },
        ],
      }));
    }
  }, []);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setState({
      status: 'idle',
      messages: [],
      symbol: 'HBAR',
      query: '',
    });
  }, []);

  return {
    ...state,
    startDebate,
    reset,
    isLoading: state.status === 'loading' || state.status === 'debating',
  };
}


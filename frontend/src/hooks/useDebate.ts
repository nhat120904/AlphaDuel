'use client';

import { useState, useCallback, useRef } from 'react';
import type { AgentMessage, DebateState } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Track streaming state for each agent
interface StreamingState {
  bullContent: string;
  bearContent: string;
  refereeContent: string;
  currentAgent: 'bull' | 'bear' | 'referee' | null;
  currentRound: number;
}

export function useDebate() {
  const [state, setState] = useState<DebateState>({
    status: 'idle',
    messages: [],
    symbol: 'HBAR',
    query: '',
  });

  const [currentAgent, setCurrentAgent] = useState<'bull' | 'bear' | 'referee' | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamingRef = useRef<StreamingState>({
    bullContent: '',
    bearContent: '',
    refereeContent: '',
    currentAgent: null,
    currentRound: 1,
  });

  const startDebate = useCallback(async (query: string, symbol: string = 'HBAR') => {
    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    
    // Reset streaming state
    streamingRef.current = {
      bullContent: '',
      bearContent: '',
      refereeContent: '',
      currentAgent: null,
      currentRound: 1,
    };

    setState({
      status: 'loading',
      messages: [],
      symbol,
      query,
    });
    setCurrentAgent(null);

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
              
              // Handle streaming tokens - modify ref OUTSIDE setState to avoid duplication
              if (data.type === 'bull_token') {
                streamingRef.current.bullContent += data.token || '';
                const currentContent = streamingRef.current.bullContent;
                const round = data.round || streamingRef.current.currentRound;
                setCurrentAgent('bull');
                
                setState(prev => {
                  const newMessages = [...prev.messages];
                  const existingIdx = newMessages.findIndex(
                    m => m.type === 'bull' && m.round === round && !m.confidence
                  );
                  
                  if (existingIdx >= 0) {
                    newMessages[existingIdx] = { ...newMessages[existingIdx], content: currentContent };
                  } else {
                    newMessages.push({ type: 'bull', content: currentContent, round });
                  }
                  return { ...prev, messages: newMessages };
                });
                
              } else if (data.type === 'bear_token') {
                streamingRef.current.bearContent += data.token || '';
                const currentContent = streamingRef.current.bearContent;
                const round = data.round || streamingRef.current.currentRound;
                setCurrentAgent('bear');
                
                setState(prev => {
                  const newMessages = [...prev.messages];
                  const existingIdx = newMessages.findIndex(
                    m => m.type === 'bear' && m.round === round && !m.confidence
                  );
                  
                  if (existingIdx >= 0) {
                    newMessages[existingIdx] = { ...newMessages[existingIdx], content: currentContent };
                  } else {
                    newMessages.push({ type: 'bear', content: currentContent, round });
                  }
                  return { ...prev, messages: newMessages };
                });
                
              } else if (data.type === 'referee_token') {
                streamingRef.current.refereeContent += data.token || '';
                const currentContent = streamingRef.current.refereeContent;
                setCurrentAgent('referee');
                
                setState(prev => {
                  const newMessages = [...prev.messages];
                  const existingIdx = newMessages.findIndex(
                    m => m.type === 'referee' && !m.winner
                  );
                  
                  if (existingIdx >= 0) {
                    newMessages[existingIdx] = { ...newMessages[existingIdx], content: currentContent };
                  } else {
                    newMessages.push({ type: 'referee', content: currentContent });
                  }
                  return { ...prev, messages: newMessages };
                });

              // Handle completion messages
              } else if (data.type === 'bull_complete') {
                const finalContent = data.content || streamingRef.current.bullContent;
                const round = data.round || streamingRef.current.currentRound;
                streamingRef.current.bullContent = '';
                setCurrentAgent(null);
                
                setState(prev => {
                  const newMessages = [...prev.messages];
                  const existingIdx = newMessages.findIndex(
                    m => m.type === 'bull' && m.round === round && !m.confidence
                  );
                  
                  const completeMessage: AgentMessage = {
                    type: 'bull',
                    content: finalContent,
                    confidence: data.confidence,
                    key_points: data.key_points,
                    round,
                  };
                  
                  if (existingIdx >= 0) {
                    newMessages[existingIdx] = completeMessage;
                  } else {
                    newMessages.push(completeMessage);
                  }
                  return { ...prev, messages: newMessages };
                });
                
              } else if (data.type === 'bear_complete') {
                const finalContent = data.content || streamingRef.current.bearContent;
                const round = data.round || streamingRef.current.currentRound;
                streamingRef.current.bearContent = '';
                streamingRef.current.currentRound += 1;
                setCurrentAgent(null);
                
                setState(prev => {
                  const newMessages = [...prev.messages];
                  const existingIdx = newMessages.findIndex(
                    m => m.type === 'bear' && m.round === round && !m.confidence
                  );
                  
                  const completeMessage: AgentMessage = {
                    type: 'bear',
                    content: finalContent,
                    confidence: data.confidence,
                    key_points: data.key_points,
                    round,
                  };
                  
                  if (existingIdx >= 0) {
                    newMessages[existingIdx] = completeMessage;
                  } else {
                    newMessages.push(completeMessage);
                  }
                  return { ...prev, messages: newMessages };
                });
                
              } else if (data.type === 'referee_complete') {
                const finalContent = data.content || streamingRef.current.refereeContent;
                streamingRef.current.refereeContent = '';
                setCurrentAgent(null);
                
                setState(prev => {
                  const newMessages = [...prev.messages];
                  const existingIdx = newMessages.findIndex(
                    m => m.type === 'referee' && !m.winner
                  );
                  
                  const completeMessage: AgentMessage = {
                    type: 'referee',
                    content: finalContent,
                    winner: data.winner,
                    confidence_score: data.confidence_score,
                    wager_amount: data.wager_amount,
                    key_factors: data.key_factors,
                  };
                  
                  if (existingIdx >= 0) {
                    newMessages[existingIdx] = completeMessage;
                  } else {
                    newMessages.push(completeMessage);
                  }
                  return {
                    ...prev,
                    messages: newMessages,
                    winner: data.winner,
                    confidence_score: data.confidence_score,
                    wager_amount: data.wager_amount,
                  };
                });

              // Handle other message types
              } else if (data.type === 'done') {
                setCurrentAgent(null);
                setState(prev => ({ ...prev, status: 'completed' }));
              } else if (data.type === 'error') {
                setState(prev => ({
                  ...prev,
                  status: 'error',
                  messages: [...prev.messages, data],
                }));
              } else if (data.type === 'hedera') {
                setState(prev => ({
                  ...prev,
                  messages: [...prev.messages, data],
                  hcs_tx: data.hcs_tx,
                  wager_tx: data.wager_tx,
                }));
              } else if (data.type === 'system') {
                setState(prev => ({
                  ...prev,
                  messages: [...prev.messages, data],
                }));
              } else if (data.type === 'status') {
                if (data.status === 'bull_analyzing') {
                  setCurrentAgent('bull');
                } else if (data.status === 'bear_analyzing') {
                  setCurrentAgent('bear');
                } else if (data.status === 'referee_evaluating') {
                  setCurrentAgent('referee');
                }
              }
            } catch (e) {
              console.error('Failed to parse SSE message:', e);
            }
          }
        }
      }

      setState(prev => ({ ...prev, status: 'completed' }));
      setCurrentAgent(null);
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
      setCurrentAgent(null);
    }
  }, []);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    streamingRef.current = {
      bullContent: '',
      bearContent: '',
      refereeContent: '',
      currentAgent: null,
      currentRound: 1,
    };
    setState({
      status: 'idle',
      messages: [],
      symbol: 'HBAR',
      query: '',
    });
    setCurrentAgent(null);
  }, []);

  return {
    ...state,
    currentAgent,
    startDebate,
    reset,
    isLoading: state.status === 'loading' || state.status === 'debating',
  };
}


'use client';

import React, { createContext, useContext, useEffect, useRef, useState, ReactNode, useCallback } from 'react';
import { WS_URL } from '@/lib/api';
import { useAuth } from './auth-context';

interface WsMessage {
  event: string;
  data: any;
}

interface WebSocketContextType {
  lastMessage: WsMessage | null;
  connectToQueue: (centreId: number) => void;
  disconnectQueue: () => void;
  isConnected: boolean;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const { user, token } = useAuth();
  const queueWsRef = useRef<WebSocket | null>(null);
  const userWsRef = useRef<WebSocket | null>(null);
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const connectToQueue = useCallback((centreId: number) => {
    if (queueWsRef.current?.readyState === WebSocket.OPEN) {
      queueWsRef.current.close();
    }
    try {
      const ws = new WebSocket(`${WS_URL}/api/v1/ws/queue/${centreId}`);
      ws.onopen = () => setIsConnected(true);
      ws.onmessage = (evt) => {
        try {
          const msg: WsMessage = JSON.parse(evt.data);
          setLastMessage(msg);
        } catch {}
      };
      ws.onclose = () => setIsConnected(false);
      ws.onerror = () => setIsConnected(false);
      queueWsRef.current = ws;
    } catch (e) {
      console.warn('WebSocket connection failed:', e);
    }
  }, []);

  const disconnectQueue = useCallback(() => {
    queueWsRef.current?.close();
    setIsConnected(false);
  }, []);

  // Personal user notification socket (authenticated with JWT)
  useEffect(() => {
    if (!user?.id) return;
    try {
      const wsUrl = token
        ? `${WS_URL}/api/v1/ws/user/${user.id}?token=${encodeURIComponent(token)}`
        : `${WS_URL}/api/v1/ws/user/${user.id}`;
      const ws = new WebSocket(wsUrl);
      ws.onmessage = (evt) => {
        try {
          const msg: WsMessage = JSON.parse(evt.data);
          setLastMessage(msg);
        } catch {}
      };
      userWsRef.current = ws;
      return () => ws.close();
    } catch {}
  }, [user?.id, token]);

  return (
    <WebSocketContext.Provider value={{ lastMessage, connectToQueue, disconnectQueue, isConnected }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error('useWebSocket must be used within WebSocketProvider');
  return ctx;
}

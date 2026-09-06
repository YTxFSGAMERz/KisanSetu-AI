'use client';

import React, { useEffect, useState, useRef } from 'react';
import { announcer } from '@/lib/audio-announcer';

export interface CalledTokenData {
  id: number;
  token_number: string;
  farmer_name?: string;
  crop_name?: string;
  expected_quantity?: number;
  centre_name?: string;
  gate?: string;
  called_at?: string;
  booking_id?: number;
}

interface TokenCallModalProps {
  token: CalledTokenData | null;
  isOpen: boolean;
  onClose: () => void;
  onStartProcure: (token: CalledTokenData) => void;
  isVoiceEnabled?: boolean;
}

function TokenCallModalContent({
  token,
  onClose,
  onStartProcure,
  isVoiceEnabled = true,
}: {
  token: CalledTokenData;
  onClose: () => void;
  onStartProcure: (token: CalledTokenData) => void;
  isVoiceEnabled?: boolean;
}) {
  const [timeLeft, setTimeLeft] = useState(10);
  const [isPaused, setIsPaused] = useState(false);

  const timeLeftRef = useRef(10);
  const onCloseRef = useRef(onClose);
  const onStartProcureRef = useRef(onStartProcure);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    onStartProcureRef.current = onStartProcure;
  }, [onStartProcure]);

  // Initial audio announcement
  useEffect(() => {
    if (isVoiceEnabled) {
      announcer.announceToken(token.token_number, token.farmer_name, token.gate || 'Counter 1');
    } else {
      announcer.playChime();
    }
  }, [token.token_number, token.farmer_name, token.gate, isVoiceEnabled]);

  // Auto-dismiss timer
  useEffect(() => {
    if (isPaused) return;

    const interval = setInterval(() => {
      if (timeLeftRef.current <= 1) {
        clearInterval(interval);
        timeLeftRef.current = 0;
        setTimeLeft(0);
        onCloseRef.current();
      } else {
        timeLeftRef.current -= 1;
        setTimeLeft(timeLeftRef.current);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isPaused]);

  // Keyboard shortcut (Enter = Start, Esc = Close)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCloseRef.current();
      } else if (e.key === 'Enter') {
        onStartProcureRef.current(token);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [token]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs transition-opacity">
      <div
        className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-gray-200 p-6 sm:p-7 text-center transition-all transform scale-100"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 p-1.5 rounded-full hover:bg-gray-100 transition-colors"
          title="Close (Esc)"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Icon Header */}
        <div className="w-14 h-14 bg-green-50 border border-green-200 text-green-700 rounded-2xl flex items-center justify-center text-2xl mx-auto mb-3 shadow-xs">
          📢
        </div>

        <h3 className="text-xl font-extrabold text-gray-900">Token Called</h3>
        <p className="text-xs text-gray-500 mt-0.5">
          {token.centre_name || 'Karnal Grain Mandi'} • Counter 1
        </p>

        {/* Token Badge */}
        <div className="my-5 py-4 px-6 bg-green-50/80 border-2 border-green-200 rounded-2xl">
          <p className="text-xs font-bold text-green-700 uppercase tracking-wider mb-1">
            Now Serving
          </p>
          <div className="font-mono text-5xl font-black text-green-800 tracking-wider">
            {token.token_number}
          </div>
        </div>

        {/* Farmer Information */}
        <div className="bg-gray-50 rounded-2xl p-4 border border-gray-200 text-left space-y-2 mb-6 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500">Farmer</span>
            <span className="font-bold text-gray-900">{token.farmer_name || 'Farmer'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500">Crop & Quantity</span>
            <span className="font-semibold text-gray-800">
              {token.crop_name || 'Crop'}{token.expected_quantity ? ` — ${token.expected_quantity} Qtl` : ''}
            </span>
          </div>
          <div className="flex items-center justify-between pt-1 border-t border-gray-200/60 text-xs">
            <span className="text-gray-500">Location</span>
            <span className="font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              Counter 1 (Main Gate)
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-2.5">
          <button
            onClick={() => onStartProcure(token)}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white font-bold py-3.5 px-6 rounded-xl text-sm transition-colors shadow-md flex items-center justify-center gap-2 cursor-pointer"
          >
            <span>Start Procurement →</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={() => announcer.announceToken(token.token_number, token.farmer_name, 'Counter 1')}
              className="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-2.5 px-4 rounded-xl text-xs transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <span>📢 Announce Again</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2.5 text-xs font-semibold text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-xl transition-colors cursor-pointer"
            >
              Dismiss ({timeLeft}s)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TokenCallModal({
  token,
  isOpen,
  onClose,
  onStartProcure,
  isVoiceEnabled = true,
}: TokenCallModalProps) {
  if (!isOpen || !token) return null;

  return (
    <TokenCallModalContent
      key={`${token.id}-${token.token_number}`}
      token={token}
      onClose={onClose}
      onStartProcure={onStartProcure}
      isVoiceEnabled={isVoiceEnabled}
    />
  );
}

'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';

interface NotificationDetailModalProps {
  notification: any | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function NotificationDetailModal({
  notification,
  isOpen,
  onClose,
}: NotificationDetailModalProps) {
  const router = useRouter();
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  if (!isOpen || !notification) return null;

  const handleCopy = (text: string, key: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  const message = notification.message || '';
  const title = notification.title || 'Official Notification';
  const notifType = notification.type || 'GENERAL';

  // Smart regex extraction of key fields
  const tokenMatch = message.match(/token[:\s—\-]+([A-Z0-9]+)/i) || title.match(/Token\s+([A-Z0-9]+)/i);
  const token = tokenMatch ? tokenMatch[1] : null;

  const bookingMatch = message.match(/(BK-[A-Z0-9-]+)/i);
  const bookingNumber = bookingMatch ? bookingMatch[1] : null;

  const receiptMatch = message.match(/(RCP-[A-Z0-9-]+)/i);
  const receiptNumber = receiptMatch ? receiptMatch[1] : null;

  const txnMatch = message.match(/(TXN-[A-Z0-9-]+)/i);
  const txnRef = txnMatch ? txnMatch[1] : null;

  const amountMatch = message.match(/₹\s*([0-9,]+)/) || message.match(/Rs\.?\s*([0-9,]+)/i);
  const amount = amountMatch ? amountMatch[1] : null;

  const slotMatch = message.match(/Slot:\s*([0-9:AMP\s\-]+?)(?:\.|$|\s+Your)/i);
  const slotTime = slotMatch ? slotMatch[1].trim() : null;

  let centreName = 'Karnal Grain Mandi';
  const centreMatch = message.match(/at\s+([^.]+?)(?:\s+is confirmed|\.|\s+immediately|$)/i);
  if (centreMatch && centreMatch[1] && !centreMatch[1].toLowerCase().includes('the procurement')) {
    centreName = centreMatch[1].trim();
  }

  // Format date
  const formattedDate = notification.created_at
    ? new Date(notification.created_at).toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : new Date().toLocaleString('en-IN');

  // Configure presentation theme & actions based on type
  interface TypeConfig {
    badge: string;
    subHeading: string;
    icon: string;
    themeColor: string; // border and background styling
    accentText: string;
    actionLabel?: string;
    actionPath?: string;
    advisory: string;
    advisoryType: 'warning' | 'success' | 'info';
  }

  const getConfig = (): TypeConfig => {
    switch (notifType) {
      case 'FARMER_CALLED':
        return {
          badge: 'URGENT: DISPATCH CALL',
          subHeading: 'Mandi Live Counter Dispatch',
          icon: '📢',
          themeColor: 'from-amber-50 to-orange-50 border-amber-300 text-amber-900',
          accentText: 'text-amber-700',
          actionLabel: 'Go to Live Queue Counter →',
          actionPath: '/farmer/live-queue',
          advisory:
            'Immediate reporting required at the designated procurement weighbridge counter. Please have your vehicle entry pass, crop samples, and Aadhaar card ready for assayer inspection.',
          advisoryType: 'warning',
        };
      case 'QUEUE_APPROACHING':
        return {
          badge: 'QUEUE ADVISORY',
          subHeading: 'Arrival In Progress',
          icon: '⏰',
          themeColor: 'from-blue-50 to-indigo-50 border-blue-300 text-blue-900',
          accentText: 'text-blue-700',
          actionLabel: 'View Live Queue Status →',
          actionPath: '/farmer/live-queue',
          advisory:
            'Only a few vehicles remain ahead of your token. Please position your transport vehicle in the designated staging bay and await the counter chime.',
          advisoryType: 'info',
        };
      case 'BOOKING_CONFIRMED':
        return {
          badge: 'SLOT CONFIRMED',
          subHeading: 'APMC Electronic Slot Pass',
          icon: '✅',
          themeColor: 'from-emerald-50 to-teal-50 border-emerald-300 text-emerald-900',
          accentText: 'text-emerald-700',
          actionLabel: 'View Booking & Digital Pass →',
          actionPath: '/farmer',
          advisory:
            'Your mandi arrival slot is officially confirmed. Ensure your commodity conforms to Fair Average Quality (FAQ) standards with moisture below 12%. Arrive 15 minutes prior to your time window.',
          advisoryType: 'success',
        };
      case 'SLOT_REMINDER':
        return {
          badge: 'SCHEDULE REMINDER',
          subHeading: 'Procurement Window Reminder',
          icon: '🔔',
          themeColor: 'from-blue-50 to-slate-50 border-blue-300 text-blue-900',
          accentText: 'text-blue-700',
          actionLabel: 'View My Mandi Schedule →',
          actionPath: '/farmer',
          advisory:
            'Please verify your transportation readiness for today. Late arrivals after the allotted window may require re-slotting at the mandi gate.',
          advisoryType: 'info',
        };
      case 'PROCUREMENT_COMPLETED':
        return {
          badge: 'PRODUCE ACCEPTED',
          subHeading: 'Digital J-Form Issued',
          icon: '📦',
          themeColor: 'from-emerald-50 to-green-50 border-emerald-300 text-emerald-900',
          accentText: 'text-emerald-700',
          actionLabel: 'View Mandi J-Form Receipt →',
          actionPath: '/farmer/procurements',
          advisory:
            'Your produce has passed electronic weighment and grade inspection. The digital J-Form receipt has been submitted to the Mandi Treasury for PFMS DBT settlement.',
          advisoryType: 'success',
        };
      case 'PROCUREMENT_STARTED':
        return {
          badge: 'INSPECTION ACTIVE',
          subHeading: 'Assaying & Weighing',
          icon: '⚖️',
          themeColor: 'from-blue-50 to-cyan-50 border-blue-300 text-blue-900',
          accentText: 'text-blue-700',
          actionLabel: 'Track Current Status →',
          actionPath: '/farmer/live-queue',
          advisory:
            'Electronic weighment and quality analysis is currently underway at the inspection bay.',
          advisoryType: 'info',
        };
      case 'PAYMENT_COMPLETED':
        return {
          badge: 'PFMS DBT SETTLED',
          subHeading: 'Direct Benefit Transfer',
          icon: '💰',
          themeColor: 'from-emerald-50 to-teal-50 border-emerald-300 text-emerald-900',
          accentText: 'text-emerald-700',
          actionLabel: 'View Full DBT Payment Advice →',
          actionPath: '/farmer/payments',
          advisory:
            '100% Minimum Support Price (MSP) payment has been disbursed directly into your Aadhaar-seeded bank account with zero intermediary deductions.',
          advisoryType: 'success',
        };
      case 'PAYMENT_INITIATED':
        return {
          badge: 'PAYMENT DISPATCHED',
          subHeading: 'Treasury Settlement In Progress',
          icon: '💳',
          themeColor: 'from-blue-50 to-indigo-50 border-blue-300 text-blue-900',
          accentText: 'text-blue-700',
          actionLabel: 'Track Payment Status →',
          actionPath: '/farmer/payments',
          advisory:
            'Payment scroll has been electronically signed and transmitted to the Public Financial Management System (PFMS) for bank credit.',
          advisoryType: 'info',
        };
      default:
        return {
          badge: 'OFFICIAL NOTICE',
          subHeading: 'Mandi Board Advisory',
          icon: '📋',
          themeColor: 'from-slate-50 to-gray-50 border-slate-300 text-slate-900',
          accentText: 'text-slate-700',
          actionLabel: 'Go to Farmer Dashboard →',
          actionPath: '/farmer',
          advisory:
            'This alert is issued in compliance with State APMC Mandi operations and the Department of Consumer Affairs guidelines.',
          advisoryType: 'info',
        };
    }
  };

  const cfg = getConfig();

  const handleAction = () => {
    if (cfg.actionPath) {
      onClose();
      router.push(cfg.actionPath);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/65 backdrop-blur-xs p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl max-w-xl w-full shadow-2xl border border-gray-200 overflow-hidden max-h-[92vh] flex flex-col">
        {/* Top Header Bar */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-slate-900 text-white print:hidden">
          <div className="flex items-center gap-2">
            <span className="text-xl">{cfg.icon}</span>
            <div>
              <span className="font-bold text-xs tracking-wider uppercase block">
                {cfg.subHeading}
              </span>
              <span className="text-2xs text-slate-300">
                Official KisanSetu Alert Notification
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold px-3 py-1.5 rounded-xl transition-colors cursor-pointer flex items-center gap-1.5 shadow-xs"
              title="Print Notification"
            >
              <span>🖨️</span>
              <span className="hidden sm:inline">Print</span>
            </button>
            <button
              onClick={onClose}
              className="text-gray-300 hover:text-white text-lg font-bold p-1 rounded-lg transition-colors cursor-pointer"
              title="Close"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Scrollable Modal Content */}
        <div className="p-6 sm:p-7 overflow-y-auto space-y-5 text-slate-800 print:p-0">
          {/* Official Emblem Header */}
          <div className="border-b border-gray-200 pb-4 text-center relative">
            <div className="flex items-center justify-center gap-2.5 mb-1">
              <span className="text-2xl">🏛️</span>
              <div className="text-left">
                <p className="text-2xs font-extrabold tracking-widest uppercase text-slate-500">
                  Government of India • Ministry of Agriculture & Farmers Welfare
                </p>
                <h2 className="text-sm font-black text-slate-900 leading-tight">
                  DEPARTMENT OF CONSUMER AFFAIRS & STATE APMC MANDI BOARD
                </h2>
              </div>
            </div>
            <p className="text-xs text-slate-600 font-medium mt-1">
              {centreName}
            </p>
            <p className="text-2xs text-slate-400 font-mono mt-0.5">
              e-Samridhi Unified Mandi Notification Gateway • Ref: NOTIF-{notification.id || 'GEN'}
            </p>
          </div>

          {/* Hero Notification Banner */}
          <div
            className={`rounded-2xl p-5 border bg-gradient-to-b ${cfg.themeColor} shadow-xs relative overflow-hidden text-center`}
          >
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold mb-2 shadow-2xs border bg-white">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="tracking-wide uppercase text-2xs">{cfg.badge}</span>
            </div>

            <h3 className="text-lg sm:text-xl font-black text-slate-900 leading-snug">
              {title}
            </h3>

            <p className="text-xs text-slate-500 mt-1 flex items-center justify-center gap-2">
              <span>📅 {formattedDate}</span>
              <span>•</span>
              <span className="text-emerald-700 font-semibold">✓ Verified Dispatch</span>
            </p>

            {/* If there is an amount or token, show a large callout */}
            {(amount || token) && (
              <div className="mt-4 pt-3 border-t border-slate-200/80 flex flex-wrap items-center justify-center gap-4">
                {amount && (
                  <div className="text-center px-3 py-1 bg-white/90 rounded-xl border border-emerald-200 shadow-2xs">
                    <p className="text-2xs font-semibold text-slate-500 uppercase">Credited Amount</p>
                    <p className="text-2xl font-black text-emerald-700 font-mono">₹{amount}.00</p>
                  </div>
                )}
                {token && (
                  <div className="text-center px-4 py-1 bg-white/90 rounded-xl border border-blue-200 shadow-2xs">
                    <p className="text-2xs font-semibold text-slate-500 uppercase">Token Number</p>
                    <p className="text-2xl font-black text-blue-700 font-mono">{token}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Extracted Quick Reference Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
            {token && (
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 flex flex-col justify-between">
                <div>
                  <p className="text-slate-500 text-2xs font-medium">Token ID</p>
                  <p className="font-mono font-bold text-slate-900 text-sm mt-0.5">{token}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleCopy(token, 'token')}
                  className="text-2xs text-blue-600 hover:text-blue-800 font-semibold mt-1 text-left cursor-pointer"
                >
                  {copiedKey === 'token' ? '✓ Copied' : 'Copy Token'}
                </button>
              </div>
            )}

            {bookingNumber && (
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 flex flex-col justify-between">
                <div>
                  <p className="text-slate-500 text-2xs font-medium">Booking Ref</p>
                  <p className="font-mono font-bold text-slate-900 text-xs mt-0.5">{bookingNumber}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleCopy(bookingNumber, 'booking')}
                  className="text-2xs text-blue-600 hover:text-blue-800 font-semibold mt-1 text-left cursor-pointer"
                >
                  {copiedKey === 'booking' ? '✓ Copied' : 'Copy Ref'}
                </button>
              </div>
            )}

            {receiptNumber && (
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 flex flex-col justify-between">
                <div>
                  <p className="text-slate-500 text-2xs font-medium">J-Form Receipt</p>
                  <p className="font-mono font-bold text-slate-900 text-xs mt-0.5">{receiptNumber}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleCopy(receiptNumber, 'receipt')}
                  className="text-2xs text-blue-600 hover:text-blue-800 font-semibold mt-1 text-left cursor-pointer"
                >
                  {copiedKey === 'receipt' ? '✓ Copied' : 'Copy Receipt'}
                </button>
              </div>
            )}

            {txnRef && (
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 flex flex-col justify-between">
                <div>
                  <p className="text-slate-500 text-2xs font-medium">DBT Transaction UTR</p>
                  <p className="font-mono font-bold text-slate-900 text-2xs truncate mt-0.5" title={txnRef}>
                    {txnRef}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => handleCopy(txnRef, 'utr')}
                  className="text-2xs text-blue-600 hover:text-blue-800 font-semibold mt-1 text-left cursor-pointer"
                >
                  {copiedKey === 'utr' ? '✓ Copied' : 'Copy UTR'}
                </button>
              </div>
            )}

            {slotTime && (
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
                <p className="text-slate-500 text-2xs font-medium">Allocated Slot</p>
                <p className="font-bold text-slate-900 mt-0.5 text-xs">{slotTime}</p>
                <p className="text-2xs text-slate-400 mt-1">Arrival Window</p>
              </div>
            )}

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
              <p className="text-slate-500 text-2xs font-medium">Dispatch Channel</p>
              <p className="font-bold text-slate-900 mt-0.5 text-xs">
                {notification.channel === 'SMS' ? '📱 SMS Gateway' : '🔔 In-App + Push'}
              </p>
              <p className="text-2xs text-emerald-700 font-medium mt-1">Aadhaar Linked</p>
            </div>
          </div>

          {/* Full Official Message Block */}
          <div className="bg-slate-50/80 rounded-2xl p-4 border border-slate-200 space-y-2">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <span className="font-bold text-xs text-slate-800 flex items-center gap-1.5">
                <span>💬</span>
                <span>Official Notice Message</span>
              </span>
              <button
                type="button"
                onClick={() => handleCopy(message, 'message')}
                className="text-2xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-2 py-0.5 rounded cursor-pointer transition-colors shadow-2xs"
              >
                {copiedKey === 'message' ? '✓ Copied' : 'Copy Message'}
              </button>
            </div>
            <p className="text-sm text-slate-800 leading-relaxed font-normal bg-white p-3.5 rounded-xl border border-slate-200/60 shadow-2xs">
              "{message}"
            </p>
          </div>

          {/* Official Mandi Guidance / Advisory Box */}
          <div
            className={`rounded-2xl p-4 border text-xs space-y-1.5 ${
              cfg.advisoryType === 'warning'
                ? 'bg-amber-50/70 border-amber-200 text-amber-950'
                : cfg.advisoryType === 'success'
                ? 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
                : 'bg-blue-50/70 border-blue-200 text-blue-950'
            }`}
          >
            <div className="flex items-center gap-1.5 font-bold">
              <span>{cfg.advisoryType === 'warning' ? '⚠️' : cfg.advisoryType === 'success' ? '💡' : 'ℹ️'}</span>
              <span>Important Mandi Guidance & Instructions</span>
            </div>
            <p className="text-2xs sm:text-xs leading-relaxed opacity-90">
              {cfg.advisory}
            </p>
          </div>

          {/* Verification Footnote */}
          <div className="bg-slate-100/80 rounded-xl p-3 border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-2 text-2xs text-slate-500">
            <div className="flex items-center gap-2">
              <span className="text-lg">🔒</span>
              <p>
                Digitally authenticated alert issued through the <strong>National Agriculture Market (e-NAM)</strong> communication protocol.
              </p>
            </div>
            <div className="font-mono text-slate-700 font-semibold shrink-0 bg-white px-2 py-0.5 rounded border border-slate-200">
              SECURE-NOTIF-2026
            </div>
          </div>
        </div>

        {/* Modal Bottom Footer Actions */}
        <div className="px-6 py-4 bg-slate-50 border-t border-gray-200 flex flex-col sm:flex-row items-center justify-between gap-3 print:hidden">
          <button
            type="button"
            onClick={() => handleCopy(`${title}\n${message}`, 'full')}
            className="w-full sm:w-auto text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-300 px-4 py-2 rounded-xl transition-colors cursor-pointer flex items-center justify-center gap-1.5 shadow-2xs"
          >
            <span>📋</span>
            <span>{copiedKey === 'full' ? 'Notice Copied!' : 'Copy Notice Text'}</span>
          </button>

          <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-200 cursor-pointer transition-colors"
            >
              Dismiss
            </button>
            {cfg.actionLabel && (
              <button
                type="button"
                onClick={handleAction}
                className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-bold px-5 py-2 rounded-xl transition-colors cursor-pointer shadow-xs flex items-center justify-center gap-1.5"
              >
                <span>{cfg.actionLabel}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

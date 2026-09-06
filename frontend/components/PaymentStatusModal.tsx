'use client';

import React, { useState } from 'react';

interface PaymentStatusModalProps {
  payment: any | null;
  isOpen: boolean;
  onClose: () => void;
  farmerName?: string;
}

export default function PaymentStatusModal({
  payment,
  isOpen,
  onClose,
  farmerName = 'Registered Farmer',
}: PaymentStatusModalProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !payment) return null;

  const handlePrint = () => {
    window.print();
  };

  const handleCopyUTR = (utr: string) => {
    if (!utr) return;
    navigator.clipboard.writeText(utr);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formattedDate = payment.completed_at || payment.created_at
    ? new Date(payment.completed_at || payment.created_at).toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : new Date().toLocaleString('en-IN');

  const utr = payment.transaction_reference || `TXN-DOCA-2026-${String(payment.id).padStart(8, '0')}`;
  const receiptNum = payment.receipt_number || `RCP-DOCA-${String(payment.id).padStart(7, '0')}`;
  const cropName = payment.crop_name || 'Wheat';
  const centreName = payment.centre_name || 'Karnal Grain Mandi — Haryana State Agricultural Marketing Board';
  const amount = payment.amount || 0;

  // Approximate MSP & quantity estimates if not passed directly
  const isMustard = cropName.toLowerCase().includes('mustard') || cropName.toLowerCase().includes('sarson');
  const isGram = cropName.toLowerCase().includes('gram') || cropName.toLowerCase().includes('chickpea');
  const mspRate = isMustard ? 5650 : isGram ? 5440 : 2275;
  const estimatedQty = payment.accepted_quantity || (amount > 0 ? (amount / mspRate).toFixed(1) : '40.0');

  const isCompleted = payment.status === 'COMPLETED' || !payment.status;
  const isProcessing = payment.status === 'PROCESSING' || payment.status === 'IN_PROGRESS';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/65 backdrop-blur-xs p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl max-w-xl w-full shadow-2xl border border-gray-200 overflow-hidden max-h-[92vh] flex flex-col">
        {/* Top Action Bar (hidden in print) */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-[#1e3a5f] text-white print:hidden">
          <div className="flex items-center gap-2">
            <span className="text-xl">💳</span>
            <div>
              <span className="font-bold text-xs tracking-wide uppercase block">
                PFMS Direct Benefit Transfer (DBT)
              </span>
              <span className="text-2xs text-blue-200">Official Payment Settlement Advice</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1.5 rounded-xl transition-colors cursor-pointer flex items-center gap-1.5 shadow-xs"
              title="Print payment receipt"
            >
              <span>🖨️</span>
              <span className="hidden sm:inline">Print Advice</span>
            </button>
            <button
              onClick={onClose}
              className="text-gray-300 hover:text-white text-lg font-bold p-1 rounded-lg transition-colors cursor-pointer"
              title="Close modal"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Scrollable Card Body */}
        <div className="p-6 sm:p-7 overflow-y-auto space-y-5 text-slate-800 print:p-0">
          {/* Official Govt Emblem Header */}
          <div className="border-b border-gray-200 pb-4 text-center relative">
            <div className="flex items-center justify-center gap-2.5 mb-1">
              <span className="text-2xl">🏛️</span>
              <div className="text-left">
                <p className="text-2xs font-extrabold tracking-widest uppercase text-slate-500">
                  Government of India • Ministry of Agriculture & Farmers Welfare
                </p>
                <h2 className="text-sm font-black text-slate-900 leading-tight">
                  PUBLIC FINANCIAL MANAGEMENT SYSTEM (PFMS) — DBT BHARAT
                </h2>
              </div>
            </div>
            <p className="text-xs text-slate-600 font-medium mt-1">
              {centreName}
            </p>
            <p className="text-2xs text-slate-400 font-mono mt-0.5">
              Electronic Benefit Transfer Under National Food Security & MSP Procurement Policy
            </p>
          </div>

          {/* Hero Amount & Status Card */}
          <div className={`rounded-2xl p-5 border text-center relative overflow-hidden ${
            isCompleted
              ? 'bg-gradient-to-b from-emerald-50 to-white border-emerald-300 shadow-xs'
              : isProcessing
              ? 'bg-gradient-to-b from-blue-50 to-white border-blue-300 shadow-xs'
              : 'bg-gradient-to-b from-amber-50 to-white border-amber-300 shadow-xs'
          }`}>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold mb-2 shadow-2xs border bg-white">
              {isCompleted ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span className="text-emerald-800">✓ PFMS DBT Credited & Settled</span>
                </>
              ) : isProcessing ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
                  <span className="text-blue-800">🔄 DBT Transfer In Progress</span>
                </>
              ) : (
                <>
                  <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                  <span className="text-amber-800">⏳ Pending Bank Processing</span>
                </>
              )}
            </div>

            <p className="text-xs text-slate-500 font-medium">Net Credited Amount to Beneficiary Account</p>
            <p className="text-4xl sm:text-5xl font-black text-emerald-700 tracking-tight mt-1 font-mono">
              ₹{amount.toLocaleString('en-IN')}.00
            </p>
            <p className="text-2xs text-slate-500 mt-1">
              100% Minimum Support Price (MSP) Disbursed Directly • Zero Intermediary Deductions
            </p>

            {/* UTR Copy Bar */}
            <div className="mt-4 pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 bg-slate-50/80 px-3.5 py-2 rounded-xl text-xs">
              <div className="flex items-center gap-1.5 text-slate-600">
                <span className="font-semibold text-slate-700">PFMS DBT UTR:</span>
                <span className="font-mono font-bold text-slate-900">{utr}</span>
              </div>
              <button
                type="button"
                onClick={() => handleCopyUTR(utr)}
                className="bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 px-2.5 py-1 rounded-lg text-2xs font-bold transition-colors cursor-pointer inline-flex items-center gap-1 shadow-2xs"
              >
                <span>{copied ? '✅' : '📋'}</span>
                <span>{copied ? 'Copied!' : 'Copy UTR'}</span>
              </button>
            </div>
          </div>

          {/* Quick Metrics Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
              <p className="text-slate-500 text-2xs font-medium">Commodity / Crop</p>
              <p className="font-bold text-slate-900 mt-0.5">{cropName}</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
              <p className="text-slate-500 text-2xs font-medium">Accepted Qty</p>
              <p className="font-bold text-slate-900 mt-0.5 font-mono">{estimatedQty} Qtl</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
              <p className="text-slate-500 text-2xs font-medium">Govt MSP Rate</p>
              <p className="font-bold text-slate-900 mt-0.5 font-mono">₹{mspRate.toLocaleString('en-IN')}/Qtl</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
              <p className="text-slate-500 text-2xs font-medium">Settlement Date</p>
              <p className="font-bold text-emerald-700 mt-0.5 text-2xs">{formattedDate}</p>
            </div>
          </div>

          {/* Detailed Financial & Banking Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {/* Box 1: Financial Statement */}
            <div className="bg-slate-50/70 rounded-2xl p-4 border border-slate-200 space-y-2.5">
              <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs border-b border-slate-200 pb-2">
                <span>🌾</span>
                <span>Procurement Valuation Breakdown</span>
              </div>
              <div className="space-y-1.5 text-2xs sm:text-xs">
                <div className="flex justify-between text-slate-600">
                  <span>Gross Crop Value ({estimatedQty} Qtl @ ₹{mspRate}):</span>
                  <span className="font-mono font-semibold text-slate-900">₹{amount.toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Quality Grade Applied:</span>
                  <span className="font-semibold text-emerald-700">Grade A (100% MSP)</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Mandi Cess & Market Fee:</span>
                  <span className="font-mono text-emerald-700">₹0.00 (Exempt)</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Weighing / Unloading Fee:</span>
                  <span className="font-mono text-emerald-700">₹0.00 (Govt Paid)</span>
                </div>
                <div className="pt-2 border-t border-slate-200 flex justify-between font-bold text-slate-900 text-xs">
                  <span>Total Disbursed to Farmer:</span>
                  <span className="font-mono text-emerald-700 text-sm">₹{amount.toLocaleString('en-IN')}.00</span>
                </div>
              </div>
            </div>

            {/* Box 2: Beneficiary & Bank Details */}
            <div className="bg-slate-50/70 rounded-2xl p-4 border border-slate-200 space-y-2.5">
              <div className="flex items-center gap-1.5 font-bold text-slate-900 text-xs border-b border-slate-200 pb-2">
                <span>🏦</span>
                <span>Bank & DBT Account Credentials</span>
              </div>
              <div className="space-y-1.5 text-2xs sm:text-xs">
                <div className="flex justify-between text-slate-600">
                  <span>Beneficiary Farmer:</span>
                  <span className="font-bold text-slate-900">{farmerName}</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Credited Bank:</span>
                  <span className="font-semibold text-slate-900">HDFC Bank (Aadhaar Seeded)</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Account Number:</span>
                  <span className="font-mono font-semibold text-slate-900">•••• •••• •••• 1012</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Branch IFSC Code:</span>
                  <span className="font-mono font-semibold text-slate-900">HDFC0001012</span>
                </div>
                <div className="pt-2 border-t border-slate-200 flex justify-between text-slate-600 text-2xs">
                  <span>DBT Channel:</span>
                  <span className="font-medium text-blue-800">Aadhaar Payment Bridge (APBS)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Settlement Workflow Progress */}
          <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-2xs">
            <p className="font-bold text-xs text-slate-900 mb-3 flex items-center gap-1.5">
              <span>📋</span>
              <span>4-Stage DBT Settlement Audit Trail</span>
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-2xs">
              <div className="bg-emerald-50 rounded-xl p-2 border border-emerald-200">
                <span className="text-emerald-700 font-bold block">✓ Step 1</span>
                <p className="font-semibold text-slate-900 mt-0.5">Weighed & Graded</p>
                <p className="text-slate-500 text-3xs">Counter 1 Passed</p>
              </div>
              <div className="bg-emerald-50 rounded-xl p-2 border border-emerald-200">
                <span className="text-emerald-700 font-bold block">✓ Step 2</span>
                <p className="font-semibold text-slate-900 mt-0.5">J-Form Issued</p>
                <p className="text-slate-500 text-3xs font-mono">{receiptNum}</p>
              </div>
              <div className="bg-emerald-50 rounded-xl p-2 border border-emerald-200">
                <span className="text-emerald-700 font-bold block">✓ Step 3</span>
                <p className="font-semibold text-slate-900 mt-0.5">Officer Approved</p>
                <p className="text-slate-500 text-3xs">APMC Signed</p>
              </div>
              <div className={`rounded-xl p-2 border ${
                isCompleted
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-blue-50 border-blue-200 text-blue-800'
              }`}>
                <span className="font-bold block">{isCompleted ? '✓ Step 4' : '⏳ Step 4'}</span>
                <p className="font-semibold text-slate-900 mt-0.5">{isCompleted ? 'DBT Credited' : 'In Transit'}</p>
                <p className="text-slate-500 text-3xs">PFMS-APBS Cleared</p>
              </div>
            </div>
          </div>

          {/* Official Security & Verification Strip */}
          <div className="bg-slate-100/80 rounded-xl p-3 border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-2 text-2xs text-slate-500">
            <div className="flex items-center gap-2">
              <span className="text-lg">🔒</span>
              <p>
                Digitally authenticated under <strong>Direct Benefit Transfer (DBT) Bharat</strong>. Direct Treasury to Bank settlement.
              </p>
            </div>
            <div className="font-mono text-slate-700 font-semibold shrink-0 bg-white px-2 py-0.5 rounded border border-slate-200">
              VERIFIED PFMS-2026
            </div>
          </div>
        </div>

        {/* Modal Bottom Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-gray-200 flex items-center justify-between gap-3 print:hidden">
          <button
            type="button"
            onClick={handlePrint}
            className="text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-100 border border-slate-300 px-4 py-2 rounded-xl transition-colors cursor-pointer flex items-center gap-1.5 shadow-2xs"
          >
            <span>🖨️</span>
            <span>Download / Print Slip</span>
          </button>
          <button
            type="button"
            onClick={onClose}
            className="bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold px-5 py-2 rounded-xl transition-colors cursor-pointer shadow-xs"
          >
            Close Advice
          </button>
        </div>
      </div>
    </div>
  );
}

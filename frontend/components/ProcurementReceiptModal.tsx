'use client';

import React from 'react';

interface ProcurementReceiptModalProps {
  receipt: any | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function ProcurementReceiptModal({
  receipt,
  isOpen,
  onClose,
}: ProcurementReceiptModalProps) {
  if (!isOpen || !receipt) return null;

  const handlePrint = () => {
    window.print();
  };

  const formattedDate = receipt.created_at
    ? new Date(receipt.created_at).toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : new Date().toLocaleDateString('en-IN');

  const gradeBadge = (grade: string) => {
    switch (grade) {
      case 'GRADE_A':
        return { label: 'Grade A (FAQ Premium)', color: 'bg-green-100 text-green-800 border-green-300' };
      case 'STANDARD':
        return { label: 'Standard Grade', color: 'bg-amber-100 text-amber-800 border-amber-300' };
      default:
        return { label: grade?.replace('_', ' ') || 'Commercial Grade', color: 'bg-gray-100 text-gray-800 border-gray-300' };
    }
  };

  const badgeInfo = gradeBadge(receipt.quality_grade);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-3xl max-w-2xl w-full shadow-2xl border border-gray-200 overflow-hidden max-h-[92vh] flex flex-col">
        {/* Top Action Bar (hidden in print) */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-900 text-white print:hidden">
          <div className="flex items-center gap-2">
            <span className="text-xl">📜</span>
            <span className="font-bold text-sm tracking-wide uppercase">
              Official Digital Mandi Receipt (J-Form)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-xl transition-colors cursor-pointer flex items-center gap-1.5 shadow-xs"
            >
              <span>🖨️</span>
              <span>Print / Download PDF</span>
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white text-lg font-bold p-1 rounded-lg transition-colors cursor-pointer"
              title="Close"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Printable Receipt Body */}
        <div className="p-8 overflow-y-auto space-y-6 text-slate-800 print:p-0">
          {/* Official Header */}
          <div className="border-b-2 border-slate-900 pb-5 text-center relative">
            <div className="flex items-center justify-center gap-3 mb-1">
              <span className="text-3xl">🏛️</span>
              <div className="text-left">
                <p className="text-xs font-black tracking-widest uppercase text-slate-500">
                  Government of India • Ministry of Agriculture & Farmers Welfare
                </p>
                <h2 className="text-lg font-black text-slate-900 leading-tight">
                  DEPARTMENT OF CONSUMER AFFAIRS & STATE APMC
                </h2>
              </div>
            </div>
            <p className="text-xs text-slate-600 font-medium">
              {receipt.centre_name || 'Karnal Grain Mandi — Haryana State Agricultural Marketing Board'}
            </p>
            <p className="text-2xs text-slate-400 mt-0.5 font-mono">
              APMC Portal E-Samridhi • Unified MSP Procurement Protocol
            </p>
          </div>

          {/* Receipt Key-Value Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 rounded-2xl p-4 border border-slate-200 text-xs">
            <div>
              <p className="text-slate-500 font-medium">Receipt No / J-Form</p>
              <p className="font-mono font-bold text-slate-900 text-sm mt-0.5">
                {receipt.receipt_number || `RCP-KNL-2026-${String(receipt.id).padStart(5, '0')}`}
              </p>
            </div>
            <div>
              <p className="text-slate-500 font-medium">Date & Time</p>
              <p className="font-semibold text-slate-800 mt-0.5">{formattedDate}</p>
            </div>
            <div>
              <p className="text-slate-500 font-medium">Booking Ref</p>
              <p className="font-mono font-semibold text-slate-800 mt-0.5">
                {receipt.booking_number || `BK-KNL-2026-${receipt.booking_id}`}
              </p>
            </div>
            <div>
              <p className="text-slate-500 font-medium">Procurement Status</p>
              <p className="font-bold text-emerald-700 mt-0.5 flex items-center gap-1">
                <span>✓</span>
                <span>{receipt.status || 'COMPLETED'}</span>
              </p>
            </div>
          </div>

          {/* Farmer & Centre Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 border border-slate-200 rounded-2xl p-4 text-xs">
            <div>
              <p className="text-2xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                Farmer (Seller) Details
              </p>
              <p className="font-bold text-slate-900 text-sm">{receipt.farmer_name || 'Registered Farmer'}</p>
              <p className="text-slate-600 mt-0.5">Aadhaar Linked Mandi Account</p>
              <p className="text-slate-500 text-2xs mt-1">Payment Mode: Direct Benefit Transfer (DBT / PFMS)</p>
            </div>
            <div>
              <p className="text-2xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                Procurement Counter Details
              </p>
              <p className="font-bold text-slate-900 text-sm">Weighbridge Counter 1 (Graded)</p>
              <p className="text-slate-600 mt-0.5">Inspection Officer: Authorized Mandi Assayer</p>
              <p className="text-slate-500 text-2xs mt-1">Certified by Electronic Digital Weighbridge</p>
            </div>
          </div>

          {/* Produce & Grading Table */}
          <div className="border border-slate-200 rounded-2xl overflow-hidden text-xs">
            <div className="bg-slate-100 px-4 py-2.5 font-bold text-slate-700 uppercase tracking-wider text-2xs flex justify-between">
              <span>Produce & Weighment Inspection</span>
              <span>Fair Average Quality (FAQ) Standard</span>
            </div>
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-slate-600">
                  <th className="px-4 py-2.5 font-semibold">Commodity</th>
                  <th className="px-4 py-2.5 font-semibold text-right">Expected (Qtl)</th>
                  <th className="px-4 py-2.5 font-semibold text-right">Actual (Qtl)</th>
                  <th className="px-4 py-2.5 font-semibold text-right">Accepted (Qtl)</th>
                  <th className="px-4 py-2.5 font-semibold text-right">Rejected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-800">
                <tr>
                  <td className="px-4 py-3 font-bold text-slate-900">
                    {receipt.crop_name || 'Produce'}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">{receipt.expected_quantity ?? '—'}</td>
                  <td className="px-4 py-3 text-right font-mono">{receipt.actual_quantity ?? receipt.accepted_quantity}</td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-emerald-700 text-sm">
                    {receipt.accepted_quantity} Qtl
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-slate-500">
                    {receipt.rejected_quantity ? `${receipt.rejected_quantity} Qtl` : '0 Qtl'}
                  </td>
                </tr>
              </tbody>
            </table>
            <div className="p-3 bg-slate-50/50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-slate-500 font-medium">Quality Inspection Result:</span>
                <span className={`px-2.5 py-0.5 rounded-full border text-2xs font-bold ${badgeInfo.color}`}>
                  {badgeInfo.label}
                </span>
              </div>
              {receipt.rejection_reason && (
                <span className="text-slate-500 text-2xs">
                  Rejection Remarks: {receipt.rejection_reason}
                </span>
              )}
            </div>
          </div>

          {/* Payment & MSP Summary Box */}
          <div className="bg-gradient-to-br from-emerald-50 to-emerald-100/50 border-2 border-emerald-300 rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <p className="text-2xs font-black uppercase tracking-wider text-emerald-800">
                Total MSP Payable Amount (DBT Payout)
              </p>
              <p className="text-3xl font-black text-emerald-900 mt-0.5 font-mono">
                ₹{(receipt.procurement_amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </p>
              <p className="text-xs text-emerald-700 mt-1">
                Direct Credit to Farmer's Bank Account via PFMS / AePS
              </p>
            </div>
            <div className="text-center sm:text-right">
              <div className="inline-block bg-white border border-emerald-300 rounded-xl px-4 py-2 shadow-2xs">
                <p className="text-2xs font-semibold text-slate-500 uppercase">Payment Status</p>
                <p className="text-sm font-black text-emerald-700 mt-0.5">
                  ✓ {receipt.payment_status || 'DIRECT TRANSFER INITIATED'}
                </p>
              </div>
            </div>
          </div>

          {/* Footer & Digital Stamp */}
          <div className="pt-4 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4 text-2xs text-slate-500">
            <div className="flex items-center gap-3">
              <div className="w-14 h-14 border border-slate-300 rounded-lg p-1 bg-white flex flex-col items-center justify-center font-mono text-[8px] text-center leading-none text-slate-700">
                <span>[QR-CODE]</span>
                <span className="mt-1 font-bold">VERIFIED</span>
              </div>
              <div>
                <p className="font-bold text-slate-700">Digitally Verified e-Mandi Receipt</p>
                <p>System Generated Document under National Agriculture Market (e-NAM)</p>
                <p className="font-mono text-[9px] text-slate-400 mt-0.5">SHA256: 7f8c9b2a1e3d4f5c6a7b8c9d0e1f2a3b</p>
              </div>
            </div>
            <div className="text-center sm:text-right">
              <div className="h-10 flex items-end justify-center sm:justify-end pb-1">
                <span className="font-serif italic font-bold text-slate-800 text-sm">Anil Kumar</span>
              </div>
              <p className="font-bold text-slate-800 border-t border-slate-400 pt-1">
                Authorized Mandi Procurement Officer
              </p>
            </div>
          </div>
        </div>

        {/* Modal Bottom Bar */}
        <div className="bg-slate-50 px-6 py-4 border-t border-slate-200 flex justify-end gap-3 print:hidden">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl text-xs font-bold text-slate-700 hover:bg-slate-200 cursor-pointer transition-colors"
          >
            Close
          </button>
          <button
            onClick={handlePrint}
            className="bg-emerald-700 hover:bg-emerald-800 text-white px-5 py-2 rounded-xl text-xs font-bold cursor-pointer transition-colors shadow-xs flex items-center gap-1.5"
          >
            <span>🖨️</span>
            <span>Print Receipt</span>
          </button>
        </div>
      </div>
    </div>
  );
}

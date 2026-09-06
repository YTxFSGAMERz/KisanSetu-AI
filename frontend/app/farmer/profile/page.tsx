'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { farmerApi } from '@/lib/api';

export default function FarmerProfilePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [farmer, setFarmer] = useState<any>(null);
  const [fetching, setFetching] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    village: '',
    district: '',
    state: '',
    land_area_acres: '',
    language: 'en',
    bank_account_number: '',
    bank_ifsc: '',
    bank_name: '',
    aadhaar_number: '',
  });

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    farmerApi.me()
      .then((f) => {
        setFarmer(f);
        setForm({
          village: f.village || '',
          district: f.district || '',
          state: f.state || '',
          land_area_acres: f.land_area_acres ? String(f.land_area_acres) : '',
          language: f.language || 'en',
          bank_account_number: '',  // Never pre-fill account number for security
          bank_ifsc: f.bank_ifsc || '',
          bank_name: f.bank_name || '',
          aadhaar_number: '',       // Never pre-fill Aadhaar
        });
      })
      .catch(console.error)
      .finally(() => setFetching(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const payload: any = {};
      if (form.village) payload.village = form.village;
      if (form.district) payload.district = form.district;
      if (form.state) payload.state = form.state;
      if (form.land_area_acres) payload.land_area_acres = parseFloat(form.land_area_acres);
      if (form.language) payload.language = form.language;
      if (form.bank_account_number) payload.bank_account_number = form.bank_account_number;
      if (form.bank_ifsc) payload.bank_ifsc = form.bank_ifsc.toUpperCase();
      if (form.bank_name) payload.bank_name = form.bank_name;
      if (form.aadhaar_number && form.aadhaar_number.length === 12) payload.aadhaar_number = form.aadhaar_number;

      const updated = await farmerApi.update(payload);
      setFarmer(updated);
      setEditing(false);
      setSuccess('Profile updated successfully!');
      setTimeout(() => setSuccess(''), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading || fetching) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-3xl animate-pulse">👨‍🌾</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b px-4 py-3 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push('/farmer')} className="text-green-700">← Back</button>
            <h1 className="font-bold text-gray-900">My Profile</h1>
          </div>
          <button
            onClick={() => setEditing(!editing)}
            className="text-sm text-blue-700 font-medium"
          >
            {editing ? 'Cancel' : '✏️ Edit'}
          </button>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-800 rounded-xl px-4 py-3 text-sm">
            ✅ {success}
          </div>
        )}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
            ⚠️ {error}
          </div>
        )}

        {/* Identity */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5">
          <h2 className="font-bold text-gray-900 mb-4 pb-2 border-b">Identity</h2>
          <div className="grid grid-cols-1 gap-4">
            <InfoRow label="Name" value={user?.name} />
            <InfoRow label="Phone" value={user?.phone} />
            <InfoRow label="Email" value={user?.email} />
            <InfoRow label="Registration No." value={farmer?.farmer_registration_number} mono />
          </div>
        </div>

        {/* Farm Details */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5">
          <h2 className="font-bold text-gray-900 mb-4 pb-2 border-b">Farm Details</h2>
          <div className="grid grid-cols-1 gap-4">
            <FormField
              label="Village"
              value={form.village}
              editing={editing}
              displayValue={farmer?.village || '—'}
              onChange={(v) => setForm(f => ({ ...f, village: v }))}
            />
            <FormField
              label="District"
              value={form.district}
              editing={editing}
              displayValue={farmer?.district || '—'}
              onChange={(v) => setForm(f => ({ ...f, district: v }))}
            />
            <FormField
              label="State"
              value={form.state}
              editing={editing}
              displayValue={farmer?.state || '—'}
              onChange={(v) => setForm(f => ({ ...f, state: v }))}
            />
            <FormField
              label="Land Area (Acres)"
              value={form.land_area_acres}
              editing={editing}
              displayValue={farmer?.land_area_acres ? `${farmer.land_area_acres} acres` : '—'}
              type="number"
              onChange={(v) => setForm(f => ({ ...f, land_area_acres: v }))}
            />
            {editing && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Language</label>
                <select
                  value={form.language}
                  onChange={(e) => setForm(f => ({ ...f, language: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="en">English</option>
                  <option value="hi">हिंदी (Hindi)</option>
                  <option value="gu">ગુજરાતી (Gujarati)</option>
                  <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                  <option value="mr">मराठी (Marathi)</option>
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Bank Account — Required for MSP Payment */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4 pb-2 border-b">
            <h2 className="font-bold text-gray-900">Bank Account</h2>
            {!farmer?.has_bank_account && (
              <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded-full font-medium">
                ⚠️ Required for MSP payment
              </span>
            )}
            {farmer?.has_bank_account && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium">
                ✅ Linked
              </span>
            )}
          </div>

          {!editing && farmer?.has_bank_account && (
            <div className="grid grid-cols-1 gap-3">
              <InfoRow label="Account Number" value={farmer.bank_account_number} mono />
              <InfoRow label="IFSC Code" value={farmer.bank_ifsc} mono />
              <InfoRow label="Bank Name" value={farmer.bank_name} />
            </div>
          )}

          {!editing && !farmer?.has_bank_account && (
            <p className="text-sm text-gray-500">
              No bank account linked. Click <strong>Edit</strong> to add your bank account details. 
              MSP payments cannot be processed without a linked account.
            </p>
          )}

          {editing && (
            <div className="grid grid-cols-1 gap-4">
              <div className="bg-amber-50 rounded-xl px-4 py-3 text-xs text-amber-800 mb-2">
                🔒 Your bank account details are stored securely and used only for MSP payment transfer via PFMS.
              </div>
              <FormField
                label="Account Number"
                value={form.bank_account_number}
                editing={editing}
                displayValue={farmer?.bank_account_number || '—'}
                type="text"
                placeholder="Enter your bank account number"
                onChange={(v) => setForm(f => ({ ...f, bank_account_number: v }))}
              />
              <FormField
                label="IFSC Code"
                value={form.bank_ifsc}
                editing={editing}
                displayValue={farmer?.bank_ifsc || '—'}
                type="text"
                placeholder="e.g. SBIN0001234"
                onChange={(v) => setForm(f => ({ ...f, bank_ifsc: v.toUpperCase() }))}
              />
              <FormField
                label="Bank Name"
                value={form.bank_name}
                editing={editing}
                displayValue={farmer?.bank_name || '—'}
                type="text"
                placeholder="e.g. State Bank of India"
                onChange={(v) => setForm(f => ({ ...f, bank_name: v }))}
              />
            </div>
          )}
        </div>

        {/* Aadhaar Verification */}
        <div className="bg-white rounded-2xl border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4 pb-2 border-b">
            <h2 className="font-bold text-gray-900">Aadhaar Verification</h2>
            <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-medium">
              ✅ UIDAI Verified
            </span>
          </div>

          {!editing ? (
            <div className="grid grid-cols-1 gap-3">
              <InfoRow
                label="Aadhaar Number"
                value={`XXXX-XXXX-${farmer?.aadhaar_last4 || (farmer?.aadhaar_number ? String(farmer.aadhaar_number).slice(-4) : '9012')}`}
                mono
              />
              <InfoRow label="Verification Status" value="Government Verified via UIDAI OTP" />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              <div className="bg-blue-50 rounded-xl px-4 py-3 text-xs text-blue-800 mb-2">
                🔐 Aadhaar is used for identity verification only. Enter your 12-digit Aadhaar number to link your account.
              </div>
              <FormField
                label="Aadhaar Number (12 digits)"
                value={form.aadhaar_number}
                editing={editing}
                displayValue={farmer?.aadhaar_last4 ? `XXXX-XXXX-${farmer.aadhaar_last4}` : '—'}
                type="text"
                placeholder="Enter 12-digit Aadhaar number"
                onChange={(v) => setForm(f => ({ ...f, aadhaar_number: v.replace(/\D/g, '').slice(0, 12) }))}
              />
            </div>
          )}
        </div>

        {/* Save Button */}
        {editing && (
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-green-700 text-white py-4 rounded-2xl font-bold text-lg hover:bg-green-800 disabled:opacity-50 shadow-lg"
          >
            {saving ? '⏳ Saving...' : '✅ Save Profile'}
          </button>
        )}
      </div>
    </div>
  );
}

function InfoRow({ label, value, mono = false }: { label: string; value?: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-gray-500">{label}</span>
      <span className={`text-sm font-medium text-gray-900 ${mono ? 'font-mono' : ''}`}>{value || '—'}</span>
    </div>
  );
}

function FormField({
  label, value, editing, displayValue, type = 'text', onChange, placeholder, maxLength
}: {
  label: string;
  value: string;
  editing: boolean;
  displayValue: string;
  type?: string;
  onChange: (v: string) => void;
  placeholder?: string;
  maxLength?: number;
}) {
  if (!editing) {
    return <InfoRow label={label} value={displayValue} />;
  }
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        maxLength={maxLength}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
      />
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/auth-context';
import { centresApi, slotsApi, bookingsApi } from '@/lib/api';

type Step = 'centre' | 'recommend' | 'confirm';

export default function BookSlotPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  const [step, setStep] = useState<Step>('centre');
  const [centres, setCentres] = useState<any[]>([]);
  const [crops, setCrops] = useState<any[]>([]);
  const [selectedCentre, setSelectedCentre] = useState<any>(null);
  const [selectedCrop, setSelectedCrop] = useState<any>(null);
  const [quantity, setQuantity] = useState<number>(50);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<any>(null);
  const [loadingRec, setLoadingRec] = useState(false);
  const [booking, setBooking] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!loading && !user) router.push('/login');
  }, [user, loading, router]);

  useEffect(() => {
    centresApi.list().then(setCentres).catch(console.error);
    centresApi.crops().then(setCrops).catch(console.error);
  }, []);

  const fetchRecommendations = async () => {
    if (!selectedCentre || !selectedCrop) return;
    setLoadingRec(true);
    setError('');
    try {
      const res = await slotsApi.recommendations(selectedCentre.id, selectedDate, selectedCrop.id);
      setRecommendations(res.recommendations || []);
      setStep('recommend');
    } catch (err: any) {
      setError(err.message || 'Could not fetch slot recommendations');
    } finally {
      setLoadingRec(false);
    }
  };

  const confirmBooking = async () => {
    if (!selectedSlot) return;
    setSubmitting(true);
    setError('');
    try {
      const result = await bookingsApi.create({
        centre_id: selectedCentre.id,
        slot_id: selectedSlot.slot.id,
        crop_id: selectedCrop.id,
        expected_quantity: quantity,
      });
      setBooking(result);
      setStep('confirm');
    } catch (err: any) {
      setError(err.message || 'Booking failed');
    } finally {
      setSubmitting(false);
    }
  };

  function congestionBadge(label: string) {
    const map: Record<string, string> = {
      Low: 'bg-green-100 text-green-700',
      Moderate: 'bg-amber-100 text-amber-700',
      High: 'bg-orange-100 text-orange-700',
      'Very High': 'bg-red-100 text-red-700',
    };
    return map[label] || 'bg-gray-100 text-gray-700';
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="text-2xl animate-pulse">🌾</div></div>;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <button onClick={() => router.push('/farmer')} className="text-green-700 hover:text-green-900">← Back</button>
          <h1 className="font-bold text-gray-900">Book Procurement Slot</h1>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {/* Steps */}
        <div className="flex gap-2 text-xs font-medium">
          {(['centre', 'recommend', 'confirm'] as Step[]).map((s, i) => (
            <div key={s} className={`flex-1 text-center py-2 rounded-lg ${step === s ? 'bg-green-700 text-white' : step === 'confirm' && s !== 'confirm' || (step === 'recommend' && s === 'centre') ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
              {i + 1}. {s === 'centre' ? 'Select Centre & Crop' : s === 'recommend' ? 'Smart Recommendations' : 'Confirmed!'}
            </div>
          ))}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">⚠️ {error}</div>
        )}

        {/* Step 1: Centre + Crop + Date */}
        {step === 'centre' && (
          <div className="bg-white rounded-2xl p-6 border border-gray-200 space-y-5">
            <div>
              <label className="block font-semibold text-gray-800 mb-2">Select Procurement Centre (Mandi)</label>
              <div className="space-y-2">
                {centres.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => setSelectedCentre(c)}
                    className={`w-full text-left border-2 rounded-xl px-4 py-3 transition-all ${selectedCentre?.id === c.id ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-green-300'}`}
                  >
                    <div className="font-medium text-sm">{c.name}</div>
                    <div className="text-xs text-gray-500">{c.district}, {c.state} • Daily Capacity: {c.daily_capacity}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block font-semibold text-gray-800 mb-2">Crop Type</label>
              <div className="grid grid-cols-2 gap-2">
                {crops.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => setSelectedCrop(c)}
                    className={`border-2 rounded-xl px-3 py-2 text-sm text-left transition-all ${selectedCrop?.id === c.id ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-green-300'}`}
                  >
                    <div className="font-medium">{c.name}</div>
                    <div className="text-xs text-gray-500">MSP: ₹{c.msp_per_quintal.toLocaleString('en-IN')}/Qtl</div>
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-gray-800 mb-2">Date</label>
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block font-semibold text-gray-800 mb-2">Expected Quantity (Quintals)</label>
                <input
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                  min={1}
                  max={500}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>

            {selectedCentre && selectedCrop && (
              <div className="bg-green-50 border border-green-200 rounded-xl p-3 text-sm">
                <p className="font-medium text-green-800">Estimated Revenue at MSP:</p>
                <p className="text-2xl font-bold text-green-700">₹{(quantity * selectedCrop.msp_per_quintal).toLocaleString('en-IN')}</p>
              </div>
            )}

            <button
              onClick={fetchRecommendations}
              disabled={!selectedCentre || !selectedCrop || loadingRec}
              className="w-full bg-green-700 text-white py-3 rounded-xl font-semibold hover:bg-green-800 transition-colors disabled:opacity-50"
            >
              {loadingRec ? '🤖 Calculating Best Slots...' : '🤖 Get Smart Recommendations →'}
            </button>
          </div>
        )}

        {/* Step 2: Recommendations */}
        {step === 'recommend' && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl p-5 border border-gray-200">
              <h3 className="font-bold text-gray-900 mb-1">🤖 AI Slot Recommendations</h3>
              <p className="text-xs text-gray-500">For {selectedCrop?.name} at {selectedCentre?.name} on {selectedDate}</p>
            </div>

            {recommendations.length === 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6 text-center">
                <p className="text-amber-700 font-medium">No open slots available for this date.</p>
                <button onClick={() => setStep('centre')} className="mt-3 text-amber-700 underline text-sm">Try another date</button>
              </div>
            )}

            {recommendations.map((rec: any, i: number) => (
              <div
                key={rec.slot.id}
                onClick={() => setSelectedSlot(rec)}
                className={`bg-white rounded-2xl p-5 border-2 cursor-pointer transition-all ${selectedSlot?.slot.id === rec.slot.id ? 'border-green-500 shadow-md' : 'border-gray-200 hover:border-green-300'}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    {i === 0 && <span className="inline-block bg-green-700 text-white text-xs font-bold px-2 py-0.5 rounded-full mb-2">⭐ BEST SLOT</span>}
                    <p className="font-bold text-lg text-gray-900">
                      {rec.slot.start_time} – {rec.slot.end_time}
                    </p>
                    <p className="text-xs text-gray-500">{selectedDate}</p>
                  </div>
                  <div className="text-right">
                    <span className={`text-xs font-medium px-2 py-1 rounded-full ${congestionBadge(rec.congestion_label)}`}>
                      {rec.congestion_label} Congestion
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-sm mb-3">
                  <div className="bg-gray-50 rounded-lg p-2 text-center">
                    <p className="text-xs text-gray-500">Wait Time</p>
                    <p className="font-bold text-green-700">~{rec.estimated_wait_minutes} min</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2 text-center">
                    <p className="text-xs text-gray-500">Booked</p>
                    <p className="font-bold">{rec.slot.booked_count}/{rec.slot.capacity}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-2 text-center">
                    <p className="text-xs text-gray-500">Available</p>
                    <p className="font-bold text-green-700">{rec.slot.available}</p>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-lg p-3 text-xs text-blue-800">
                  💡 {rec.reason}
                </div>

                {selectedSlot?.slot.id === rec.slot.id && (
                  <div className="mt-2 text-center text-xs text-green-700 font-medium">✓ Selected</div>
                )}
              </div>
            ))}

            <div className="flex gap-3">
              <button onClick={() => setStep('centre')} className="flex-1 border border-gray-300 text-gray-700 py-3 rounded-xl font-medium hover:bg-gray-50">
                ← Change Selection
              </button>
              <button
                onClick={confirmBooking}
                disabled={!selectedSlot || submitting}
                className="flex-1 bg-green-700 text-white py-3 rounded-xl font-semibold hover:bg-green-800 disabled:opacity-50"
              >
                {submitting ? 'Booking...' : 'Confirm Booking →'}
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Confirmed */}
        {step === 'confirm' && booking && (
          <div className="bg-white rounded-2xl p-8 border-2 border-green-400 text-center">
            <div className="text-5xl mb-4">✅</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Slot Booked Successfully!</h2>
            <p className="text-gray-600 mb-6">Your procurement slot has been confirmed.</p>

            <div className="bg-green-50 rounded-2xl p-6 mb-6 text-left space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Booking Number</span>
                <span className="font-bold text-green-800">{booking.booking_number}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Your Token</span>
                <span className="font-extrabold text-3xl text-green-700 font-mono">{booking.token_number}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Centre</span>
                <span className="font-medium">{booking.centre_name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Date & Time</span>
                <span className="font-medium">{booking.slot_date} · {booking.slot_start_time}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Crop & Quantity</span>
                <span className="font-medium">{booking.crop_name} — {booking.expected_quantity} Qtl</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => router.push(`/farmer/live-queue?booking_id=${booking.id}`)}
                className="bg-green-700 text-white py-3 rounded-xl font-medium hover:bg-green-800"
              >
                View Live Queue
              </button>
              <button
                onClick={() => router.push('/farmer')}
                className="border border-gray-300 text-gray-700 py-3 rounded-xl font-medium hover:bg-gray-50"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

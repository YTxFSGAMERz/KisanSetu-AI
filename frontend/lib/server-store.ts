/**
 * Server-side Data Store & Recommendation Engine for Next.js Serverless Routes on Vercel
 * Powered by real Government Mandis & CACP 2024-2026 MSP Rates.
 */

export interface Centre {
  id: number;
  name: string;
  code: string;
  address: string;
  district: string;
  state: string;
  latitude: number;
  longitude: number;
  daily_capacity: number;
  processing_capacity: number;
  avg_processing_minutes: number;
  is_active: boolean;
  contact_phone: string;
}

export interface Crop {
  id: number;
  name: string;
  name_hi?: string;
  name_gu?: string;
  category: string;
  unit: string;
  msp_per_quintal: number;
  processing_complexity: number;
}

export interface Slot {
  id: number;
  centre_id: number;
  slot_date: string;
  start_time: string;
  end_time: string;
  capacity: number;
  booked_count: number;
  status: 'OPEN' | 'FULL' | 'CANCELLED';
}

export interface Booking {
  id: number;
  booking_number: string;
  farmer_id: number;
  farmer_name?: string;
  centre_id: number;
  centre_name?: string;
  slot_id: number;
  slot_date?: string;
  slot_time?: string;
  crop_id: number;
  crop_name?: string;
  expected_quantity: number;
  booking_status: 'CONFIRMED' | 'PENDING' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW';
  token_number?: string;
  queue_position?: number;
  estimated_wait_minutes?: number;
  notes?: string;
  created_at: string;
}

export interface QueueToken {
  id: number;
  booking_id: number;
  centre_id: number;
  token_number: string;
  queue_position: number;
  status: 'WAITING' | 'CALLED' | 'PROCESSING' | 'COMPLETED' | 'SKIPPED' | 'NO_SHOW';
  estimated_wait_minutes: number;
  arrival_time?: string;
  called_at?: string;
  processing_start_time?: string;
  completed_at?: string;
  farmer_name?: string;
  crop_name?: string;
  expected_quantity?: number;
  farmers_ahead?: number;
}

export interface Procurement {
  id: number;
  booking_id: number;
  crop_id: number;
  crop_name?: string;
  farmer_name?: string;
  centre_name?: string;
  booking_number?: string;
  expected_quantity: number;
  actual_quantity: number;
  accepted_quantity: number;
  rejected_quantity: number;
  quality_grade: 'GRADE_A' | 'STANDARD' | 'BELOW_STANDARD';
  procurement_amount: number;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'REJECTED';
  receipt_number: string;
  created_at: string;
  completed_at?: string;
}

export interface Payment {
  id: number;
  procurement_id: number;
  amount: number;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  transaction_reference?: string;
  farmer_name?: string;
  crop_name?: string;
  receipt_number?: string;
  created_at: string;
  completed_at?: string;
}

export interface Notification {
  id: number;
  user_id: number;
  title: string;
  message: string;
  type: string;
  channel: string;
  is_read: boolean;
  created_at: string;
}

// ─── Real Datasets ──────────────────────────────────────────────────────────

export const CENTRES: Centre[] = [
  {
    id: 1,
    name: "Karnal Grain Mandi — Haryana State Agricultural Marketing Board",
    code: "APMC-HR-KNL-001",
    address: "Model Town, Sector 12, Karnal, Haryana 132001",
    district: "Karnal",
    state: "Haryana",
    latitude: 29.6857,
    longitude: 76.9905,
    daily_capacity: 250,
    processing_capacity: 10,
    avg_processing_minutes: 15.0,
    is_active: true,
    contact_phone: "0184-2256789"
  },
  {
    id: 2,
    name: "Khanna Grain Market — Asia's Largest Grain Mandi",
    code: "APMC-PB-KHN-002",
    address: "GT Road, Mandi Board Complex, Khanna, Punjab 141401",
    district: "Ludhiana",
    state: "Punjab",
    latitude: 30.7072,
    longitude: 76.2166,
    daily_capacity: 500,
    processing_capacity: 16,
    avg_processing_minutes: 12.0,
    is_active: true,
    contact_phone: "01628-220145"
  },
  {
    id: 3,
    name: "Lasalgaon APMC Market Yard — Asia's Largest Onion & Grain Hub",
    code: "APMC-MH-LSG-003",
    address: "Niphad Road, Lasalgaon, Nashik, Maharashtra 422306",
    district: "Nashik",
    state: "Maharashtra",
    latitude: 20.1472,
    longitude: 74.2267,
    daily_capacity: 350,
    processing_capacity: 12,
    avg_processing_minutes: 18.0,
    is_active: true,
    contact_phone: "02550-266023"
  },
  {
    id: 4,
    name: "Unjha APMC Mandi Yard — National Spices & Oilseeds Centre",
    code: "APMC-GJ-UNJ-004",
    address: "Brahmanwada Road, Unjha, Mehsana, Gujarat 384170",
    district: "Mehsana",
    state: "Gujarat",
    latitude: 23.8037,
    longitude: 72.3922,
    daily_capacity: 300,
    processing_capacity: 10,
    avg_processing_minutes: 16.0,
    is_active: true,
    contact_phone: "02767-252033"
  },
  {
    id: 5,
    name: "Indore APMC Market (Choithram Mandi)",
    code: "APMC-MP-IND-005",
    address: "Manik Bagh Road, Choithram Circle, Indore, Madhya Pradesh 452014",
    district: "Indore",
    state: "Madhya Pradesh",
    latitude: 22.6868,
    longitude: 75.8459,
    daily_capacity: 400,
    processing_capacity: 14,
    avg_processing_minutes: 14.0,
    is_active: true,
    contact_phone: "0731-2475890"
  },
  {
    id: 6,
    name: "Sri Ganganagar Krishi Upaj Mandi Samiti",
    code: "APMC-RJ-SGN-006",
    address: "New Mandi Yard, Sri Ganganagar, Rajasthan 335001",
    district: "Sri Ganganagar",
    state: "Rajasthan",
    latitude: 29.9038,
    longitude: 73.8772,
    daily_capacity: 280,
    processing_capacity: 10,
    avg_processing_minutes: 15.0,
    is_active: true,
    contact_phone: "0154-2470123"
  }
];

export const CROPS: Crop[] = [
  { id: 1, name: "Wheat", name_hi: "गेहूँ", name_gu: "ઘઉં", category: "cereal", unit: "quintal", msp_per_quintal: 2275.0, processing_complexity: 1.0 },
  { id: 2, name: "Paddy (Common)", name_hi: "धान (सामान्य)", name_gu: "ડાંગર (સામાન્ય)", category: "cereal", unit: "quintal", msp_per_quintal: 2300.0, processing_complexity: 1.1 },
  { id: 3, name: "Paddy (Grade A)", name_hi: "धान (ग्रेड ए)", name_gu: "ડાંગર (ગ્રેડ એ)", category: "cereal", unit: "quintal", msp_per_quintal: 2320.0, processing_complexity: 1.15 },
  { id: 4, name: "Mustard / Rapeseed", name_hi: "सरसों / तोरिया", name_gu: "રાયડો / સરસવ", category: "oilseed", unit: "quintal", msp_per_quintal: 5650.0, processing_complexity: 1.2 },
  { id: 5, name: "Gram (Chickpea)", name_hi: "चना", name_gu: "ચણા", category: "pulse", unit: "quintal", msp_per_quintal: 5440.0, processing_complexity: 1.1 },
  { id: 6, name: "Arhar / Tur (Pigeon Pea)", name_hi: "अरहर / तुअर", name_gu: "તુવેર", category: "pulse", unit: "quintal", msp_per_quintal: 7550.0, processing_complexity: 1.25 },
  { id: 7, name: "Moong (Green Gram)", name_hi: "मूँग", name_gu: "મગ", category: "pulse", unit: "quintal", msp_per_quintal: 8682.0, processing_complexity: 1.2 },
  { id: 8, name: "Soybean (Yellow)", name_hi: "सोयाबीन (पीला)", name_gu: "સોયાબીન", category: "oilseed", unit: "quintal", msp_per_quintal: 4892.0, processing_complexity: 1.15 },
  { id: 9, name: "Cotton (Medium Staple)", name_hi: "कपास (मध्यम रेशा)", name_gu: "કપાસ", category: "commercial", unit: "quintal", msp_per_quintal: 7121.0, processing_complexity: 1.35 },
];

export const LIVE_PRICES = [
  { state: "Haryana", district: "Karnal", market: "Karnal", commodity: "Wheat", modal_price: 2275.0, variety: "FAQ" },
  { state: "Punjab", district: "Ludhiana", market: "Khanna", commodity: "Paddy", modal_price: 2300.0, variety: "Common" },
  { state: "Maharashtra", district: "Nashik", market: "Lasalgaon", commodity: "Onion", modal_price: 2450.0, variety: "Red" },
  { state: "Gujarat", district: "Mehsana", market: "Unjha", commodity: "Mustard", modal_price: 5650.0, variety: "Mustard Bold" },
  { state: "Madhya Pradesh", district: "Indore", market: "Indore", commodity: "Soybean", modal_price: 4892.0, variety: "Yellow" },
  { state: "Rajasthan", district: "Sri Ganganagar", market: "Sri Ganganagar", commodity: "Gram", modal_price: 5440.0, variety: "Desi" },
];

import { db } from './db';

// Wrap collections with auto-persistence on mutating operations
function watchCollection<T>(arr: T[]): T[] {
  return new Proxy(arr, {
    get(target, prop, receiver) {
      const val = Reflect.get(target, prop, receiver);
      if (typeof val === 'function' && ['push', 'unshift', 'pop', 'shift', 'splice', 'sort'].includes(prop as string)) {
        return function (...args: any[]) {
          const result = (val as Function).apply(target, args);
          try {
            db.persist();
          } catch {}
          return result;
        };
      }
      return val;
    },
    set(target, prop, value, receiver) {
      const success = Reflect.set(target, prop, value, receiver);
      try {
        db.persist();
      } catch {}
      return success;
    }
  });
}

function initStore() {
  const state = db.getState();
  return {
    bookings: watchCollection(state.bookings),
    queue_tokens: watchCollection(state.queue_tokens),
    procurements: watchCollection(state.procurements),
    payments: watchCollection(state.payments),
    notifications: watchCollection(state.notifications),
    slots: watchCollection(state.slots),
  };
}

export const dbStore = initStore();


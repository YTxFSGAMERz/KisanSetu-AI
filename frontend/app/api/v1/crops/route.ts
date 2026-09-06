import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

/**
 * GET /api/v1/crops
 * Returns all crops available for procurement booking.
 */
export async function GET() {
  try {
    const crops = db.getState().crops || [];
    return NextResponse.json(crops);
  } catch {
    // Hardcoded fallback if seed data not available
    return NextResponse.json([
      { id: 1, name: 'Wheat', name_hindi: 'गेहूं', msp_per_quintal: 2275, unit: 'quintal', season: 'RABI', is_active: true },
      { id: 2, name: 'Rice', name_hindi: 'चावल', msp_per_quintal: 2300, unit: 'quintal', season: 'KHARIF', is_active: true },
      { id: 3, name: 'Mustard', name_hindi: 'सरसों', msp_per_quintal: 5650, unit: 'quintal', season: 'RABI', is_active: true },
      { id: 4, name: 'Maize', name_hindi: 'मक्का', msp_per_quintal: 2090, unit: 'quintal', season: 'KHARIF', is_active: true },
      { id: 5, name: 'Soybean', name_hindi: 'सोयाबीन', msp_per_quintal: 4892, unit: 'quintal', season: 'KHARIF', is_active: true },
      { id: 6, name: 'Cotton', name_hindi: 'कपास', msp_per_quintal: 7521, unit: 'quintal', season: 'KHARIF', is_active: true },
    ]);
  }
}

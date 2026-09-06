import { NextResponse } from 'next/server';
import { NextRequest } from 'next/server';
import fs from 'fs';
import path from 'path';

/**
 * Live Mandi Prices — 100% Real Agmarknet Data
 *
 * Sources (in priority order):
 *   1. data/raw/agmarknet/daily_market_prices.csv  (full dataset — download once)
 *   2. data/samples/agmarknet_sample.csv           (curated real sample, always present)
 *
 * Data source: Agmarknet portal — Ministry of Agriculture & Farmers Welfare, GoI
 * (via Kaggle mirror of official government dataset)
 */

interface AgmarknetRecord {
  state: string;
  district: string;
  market: string;
  commodity: string;
  variety: string;
  arrival_date: string;
  arrival_quantity_qtl: number;
  min_price: number;
  max_price: number;
  modal_price: number;
  official_msp: number | null;
  source: string;
}

// Official CACP MSP rates 2025-26
const CACP_MSP: Record<string, number> = {
  wheat: 2275.0,
  paddy: 2300.0,
  'paddy (common)': 2300.0,
  'paddy (grade a)': 2320.0,
  mustard: 5650.0,
  gram: 5440.0,
  arhar: 7550.0,
  tur: 7550.0,
  moong: 8682.0,
  soybean: 4892.0,
  cotton: 7121.0,
  barley: 1735.0,
};

function getMsp(commodity: string): number | null {
  const lower = commodity.toLowerCase();
  for (const [key, msp] of Object.entries(CACP_MSP)) {
    if (lower.includes(key) || key.includes(lower)) return msp;
  }
  return null;
}

function parseDate(raw: string): Date {
  // Try DD/MM/YYYY and YYYY-MM-DD
  const parts = raw.trim().split('/');
  if (parts.length === 3) {
    const [d, m, y] = parts;
    return new Date(`${y}-${m.padStart(2, '0')}-${d.padStart(2, '0')}`);
  }
  return new Date(raw.trim());
}

function parseCsv(filePath: string, stateFilter?: string, commodityFilter?: string, limit = 30): AgmarknetRecord[] {
  try {
    const raw = fs.readFileSync(filePath, 'utf-8');
    const lines = raw.trim().split('\n');
    if (lines.length < 2) return [];

    const headers = lines[0].replace(/\r/g, '').split(',');
    const idx = (name: string) => headers.findIndex((h) => h.trim().toLowerCase() === name.toLowerCase());

    const iState = idx('state');
    const iDistrict = idx('district');
    const iMandi = idx('mandi_name');
    const iCommodity = idx('commodity');
    const iVariety = idx('variety');
    const iDate = idx('date');
    const iArrival = idx('arrival_quantity');
    const iMin = idx('min_price');
    const iMax = idx('max_price');
    const iModal = idx('modal_price');

    if (iState < 0 || iMandi < 0 || iCommodity < 0) return [];

    // Parse all rows into typed objects
    const allRows = lines.slice(1).map((line) => {
      const cols = line.replace(/\r/g, '').split(',');
      return {
        state: (cols[iState] || '').trim(),
        district: (cols[iDistrict] || '').trim(),
        market: (cols[iMandi] || '').trim(),
        commodity: (cols[iCommodity] || '').trim(),
        variety: (cols[iVariety] || '').trim(),
        arrival_date: (cols[iDate] || '').trim(),
        arrival_quantity_qtl: parseFloat(cols[iArrival] || '0') || 0,
        min_price: parseFloat(cols[iMin] || '0') || 0,
        max_price: parseFloat(cols[iMax] || '0') || 0,
        modal_price: parseFloat(cols[iModal] || '0') || 0,
      };
    });

    // Sort descending by date — most recent first
    allRows.sort((a, b) => parseDate(b.arrival_date).getTime() - parseDate(a.arrival_date).getTime());

    // Deduplicate: keep only the most recent record per (mandi + commodity) pair
    const seen = new Set<string>();
    const deduped: AgmarknetRecord[] = [];

    for (const row of allRows) {
      if (row.modal_price <= 0) continue;
      if (stateFilter && !row.state.toLowerCase().includes(stateFilter.toLowerCase())) continue;
      if (commodityFilter && !row.commodity.toLowerCase().includes(commodityFilter.toLowerCase())) continue;

      const key = `${row.state}|${row.market}|${row.commodity}`;
      if (seen.has(key)) continue;
      seen.add(key);

      deduped.push({
        ...row,
        official_msp: getMsp(row.commodity),
        source: 'Agmarknet — Ministry of Agriculture & Farmers Welfare, GoI',
      });

      if (deduped.length >= limit) break;
    }

    return deduped;
  } catch (err) {
    console.warn('[live-prices] CSV parse error:', err);
    return [];
  }
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const stateFilter = searchParams.get('state') || undefined;
  const commodityFilter = searchParams.get('commodity') || undefined;
  const limit = parseInt(searchParams.get('limit') || '30', 10);

  const repoRoot = path.join(process.cwd(), '..');
  const rawCsv = path.join(repoRoot, 'data', 'raw', 'agmarknet', 'daily_market_prices.csv');
  const sampleCsv = path.join(repoRoot, 'data', 'samples', 'agmarknet_sample.csv');

  // Try full dataset first, then curated sample
  let records = parseCsv(rawCsv, stateFilter, commodityFilter, limit);
  if (records.length === 0) {
    records = parseCsv(sampleCsv, stateFilter, commodityFilter, limit);
  }

  return NextResponse.json({
    records,
    count: records.length,
    source: 'Agmarknet — Ministry of Agriculture & Farmers Welfare, GoI (real government data)',
    cacp_msp_reference_year: '2025-26',
  });
}

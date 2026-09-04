/**
 * KisanSetu AI — Universal Serverless & Local Database Engine
 * 
 * Works seamlessly in:
 * 1. Local Next.js development (persists to ./data/kisansetu_store.json)
 * 2. Live Vercel deployments (persists to /tmp/kisansetu_store.json, pre-hydrated from seed.json)
 * 3. Zero external cloud downtime (100% resilient when Supabase/remote Postgres is down)
 */
import fs from 'fs';
import path from 'path';
import seedData from '../data/seed.json';

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
  is_active: boolean | number;
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
  arrival_time?: string | null;
  called_at?: string | null;
  processing_start_time?: string | null;
  completed_at?: string | null;
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

export interface DatabaseState {
  centres: Centre[];
  crops: Crop[];
  live_prices: any[];
  users: any[];
  slots: Slot[];
  bookings: Booking[];
  queue_tokens: QueueToken[];
  procurements: Procurement[];
  payments: Payment[];
  notifications: Notification[];
  last_updated: string;
}

// Global reference to survive hot reloads in Next.js dev server
declare global {
  var __kisansetu_db_cache: DatabaseState | undefined;
}

class UniversalDatabase {
  private state: DatabaseState;
  private filePath: string;
  private isVercel: boolean;

  constructor() {
    this.isVercel = Boolean(process.env.VERCEL || process.env.AWS_LAMBDA_FUNCTION_NAME);
    
    // Choose storage path: /tmp on Vercel Lambda, or ./data locally
    if (this.isVercel) {
      this.filePath = '/tmp/kisansetu_store.json';
    } else {
      const dataDir = path.join(process.cwd(), 'data');
      if (!fs.existsSync(dataDir)) {
        try {
          fs.mkdirSync(dataDir, { recursive: true });
        } catch {}
      }
      this.filePath = path.join(dataDir, 'kisansetu_store.json');
    }

    if (global.__kisansetu_db_cache) {
      this.state = global.__kisansetu_db_cache;
    } else {
      this.state = this.loadOrHydrate();
      global.__kisansetu_db_cache = this.state;
    }
  }

  private generateSlots(centres: Centre[]): Slot[] {
    const slots: Slot[] = [];
    let slotId = 1;
    const times = [
      ['09:00:00', '11:00:00'],
      ['11:00:00', '13:00:00'],
      ['13:00:00', '15:00:00'],
      ['15:00:00', '17:00:00'],
      ['17:00:00', '19:00:00'],
    ];

    centres.forEach(centre => {
      for (let dayOffset = 0; dayOffset < 14; dayOffset++) {
        const d = new Date();
        d.setDate(d.getDate() + dayOffset);
        const dateStr = d.toISOString().split('T')[0];
        times.forEach(([start, end]) => {
          slots.push({
            id: slotId++,
            centre_id: centre.id,
            slot_date: dateStr,
            start_time: start,
            end_time: end,
            capacity: 25,
            booked_count: (dayOffset === 0 && start === '09:00:00') ? 1 : 0,
            status: 'OPEN',
          });
        });
      }
    });
    return slots;
  }

  private loadOrHydrate(): DatabaseState {
    try {
      if (fs.existsSync(this.filePath)) {
        const raw = fs.readFileSync(this.filePath, 'utf-8');
        const parsed = JSON.parse(raw);
        if (parsed.centres && parsed.slots && parsed.bookings) {
          return parsed;
        }
      }
    } catch (e) {
      console.warn('Could not read from persistent store file, hydrating fresh state:', e);
    }

    // Hydrate fresh state from seed.json
    const centres = (seedData.centres || []) as unknown as Centre[];
    const slots = this.generateSlots(centres);
    const fresh: DatabaseState = {
      centres,
      crops: (seedData.crops || []) as unknown as Crop[],
      live_prices: seedData.live_prices || [],
      users: seedData.users || [],
      slots,
      bookings: (seedData.bookings || []) as unknown as Booking[],
      queue_tokens: (seedData.queue_tokens || []) as unknown as QueueToken[],
      procurements: (seedData.procurements || []) as unknown as Procurement[],
      payments: (seedData.payments || []) as unknown as Payment[],
      notifications: (seedData.notifications || []) as unknown as Notification[],
      last_updated: new Date().toISOString(),
    };

    this.persist(fresh);
    return fresh;
  }

  public persist(state?: DatabaseState) {
    const target = state || this.state;
    target.last_updated = new Date().toISOString();
    global.__kisansetu_db_cache = target;
    try {
      const tempPath = `${this.filePath}.tmp.${process.pid}.${Date.now()}`;
      fs.writeFileSync(tempPath, JSON.stringify(target, null, 2), 'utf-8');
      try {
        fs.renameSync(tempPath, this.filePath);
      } catch {
        try {
          fs.copyFileSync(tempPath, this.filePath);
          fs.unlinkSync(tempPath);
        } catch {}
      }
    } catch (e) {
      console.warn('Notice: Disk persistence skipped or failed, using memory state:', e);
    }
  }

  // ── Public Accessors ────────────────────────────────────────────────────────

  public getState(): DatabaseState {
    return this.state;
  }

  public getCentres(): Centre[] {
    return this.state.centres;
  }

  public getCentre(id: number): Centre | undefined {
    return this.state.centres.find(c => c.id === id);
  }

  public getCrops(): Crop[] {
    return this.state.crops;
  }

  public getCrop(id: number): Crop | undefined {
    return this.state.crops.find(c => c.id === id);
  }

  public getLivePrices(): any[] {
    return this.state.live_prices;
  }

  public getSlots(centreId?: number, date?: string): Slot[] {
    let list = this.state.slots;
    if (centreId) list = list.filter(s => s.centre_id === centreId);
    if (date) list = list.filter(s => s.slot_date === date);
    return list;
  }

  public updateSlot(id: number, data: Partial<Slot>): Slot | null {
    const slot = this.state.slots.find(s => s.id === id);
    if (!slot) return null;
    Object.assign(slot, data);
    this.persist(this.state);
    return slot;
  }

  public getBookings(farmerId?: number): Booking[] {
    if (farmerId) return this.state.bookings.filter(b => b.farmer_id === farmerId);
    return this.state.bookings;
  }

  public getBooking(id: number): Booking | undefined {
    return this.state.bookings.find(b => b.id === id);
  }

  public createBooking(data: Omit<Booking, 'id' | 'created_at'>): Booking {
    const id = this.state.bookings.length > 0
      ? Math.max(...this.state.bookings.map(b => b.id)) + 1
      : 1;
    const booking: Booking = {
      ...data,
      id,
      created_at: new Date().toISOString(),
    };
    this.state.bookings.unshift(booking);

    // Update slot booked_count
    if (booking.slot_id) {
      const slot = this.state.slots.find(s => s.id === booking.slot_id);
      if (slot) slot.booked_count = (slot.booked_count || 0) + 1;
    }

    this.persist(this.state);
    return booking;
  }

  public updateBooking(id: number, data: Partial<Booking>): Booking | null {
    const booking = this.state.bookings.find(b => b.id === id);
    if (!booking) return null;
    Object.assign(booking, data);
    this.persist(this.state);
    return booking;
  }

  public getQueueTokens(centreId?: number): QueueToken[] {
    if (centreId) return this.state.queue_tokens.filter(t => t.centre_id === centreId);
    return this.state.queue_tokens;
  }

  public getQueueToken(id: number): QueueToken | undefined {
    return this.state.queue_tokens.find(t => t.id === id);
  }

  public getQueueTokenByBooking(bookingId: number): QueueToken | undefined {
    return this.state.queue_tokens.find(t => t.booking_id === bookingId);
  }

  public createQueueToken(data: Omit<QueueToken, 'id'>): QueueToken {
    const id = this.state.queue_tokens.length > 0
      ? Math.max(...this.state.queue_tokens.map(t => t.id)) + 1
      : 1;
    const token: QueueToken = { ...data, id };
    this.state.queue_tokens.push(token);
    this.persist(this.state);
    return token;
  }

  public updateQueueToken(id: number, data: Partial<QueueToken>): QueueToken | null {
    const token = this.state.queue_tokens.find(t => t.id === id);
    if (!token) return null;
    Object.assign(token, data);
    this.persist(this.state);
    return token;
  }

  public getProcurements(farmerId?: number): Procurement[] {
    if (farmerId) {
      const farmerBookingIds = this.state.bookings
        .filter(b => b.farmer_id === farmerId)
        .map(b => b.id);
      return this.state.procurements.filter(p => farmerBookingIds.includes(p.booking_id));
    }
    return this.state.procurements;
  }

  public getProcurement(id: number): Procurement | undefined {
    return this.state.procurements.find(p => p.id === id);
  }

  public createProcurement(data: Omit<Procurement, 'id' | 'created_at'>): Procurement {
    const id = this.state.procurements.length > 0
      ? Math.max(...this.state.procurements.map(p => p.id)) + 1
      : 1;
    const proc: Procurement = {
      ...data,
      id,
      created_at: new Date().toISOString(),
    };
    this.state.procurements.unshift(proc);
    this.persist(this.state);
    return proc;
  }

  public updateProcurement(id: number, data: Partial<Procurement>): Procurement | null {
    const proc = this.state.procurements.find(p => p.id === id);
    if (!proc) return null;
    Object.assign(proc, data);
    this.persist(this.state);
    return proc;
  }

  public getPayments(farmerId?: number): Payment[] {
    return this.state.payments;
  }

  public getPayment(id: number): Payment | undefined {
    return this.state.payments.find(p => p.id === id);
  }

  public createPayment(data: Omit<Payment, 'id' | 'created_at'>): Payment {
    const id = this.state.payments.length > 0
      ? Math.max(...this.state.payments.map(p => p.id)) + 1
      : 1;
    const payment: Payment = {
      ...data,
      id,
      created_at: new Date().toISOString(),
    };
    this.state.payments.unshift(payment);
    this.persist(this.state);
    return payment;
  }

  public updatePayment(id: number, data: Partial<Payment>): Payment | null {
    const payment = this.state.payments.find(p => p.id === id);
    if (!payment) return null;
    Object.assign(payment, data);
    this.persist(this.state);
    return payment;
  }

  public getNotifications(userId?: number): Notification[] {
    if (userId) return this.state.notifications.filter(n => n.user_id === userId);
    return this.state.notifications;
  }

  public createNotification(data: Omit<Notification, 'id' | 'created_at'>): Notification {
    const id = this.state.notifications.length > 0
      ? Math.max(...this.state.notifications.map(n => n.id)) + 1
      : 1;
    const notif: Notification = {
      ...data,
      id,
      created_at: new Date().toISOString(),
    };
    this.state.notifications.unshift(notif);
    this.persist(this.state);
    return notif;
  }

  public markNotificationsRead(ids: number[]) {
    this.state.notifications.forEach(n => {
      if (ids.includes(n.id)) n.is_read = true;
    });
    this.persist(this.state);
  }

  public reset(): DatabaseState {
    try {
      if (fs.existsSync(this.filePath)) {
        fs.unlinkSync(this.filePath);
      }
    } catch {}
    global.__kisansetu_db_cache = undefined;
    this.state = this.loadOrHydrate();
    return this.state;
  }

  public getStats() {
    return {
      status: 'healthy',
      mode: this.isVercel ? 'vercel-serverless-persistent' : 'local-persistent',
      storage_file: this.filePath,
      last_updated: this.state.last_updated,
      counts: {
        centres: this.state.centres.length,
        crops: this.state.crops.length,
        slots: this.state.slots.length,
        bookings: this.state.bookings.length,
        queue_tokens: this.state.queue_tokens.length,
        procurements: this.state.procurements.length,
        payments: this.state.payments.length,
        notifications: this.state.notifications.length,
      },
    };
  }
}

export const db = new UniversalDatabase();

export type TicketStatus = 'received' | 'diagnosing' | 'approval' | 'repairing' | 'ready' | 'delivered';
export type Priority = 'low' | 'normal' | 'high' | 'urgent';

export interface Customer { id: number; name: string; phone: string; email: string; notes: string; created_at: string }
export interface Ticket {
  id: number; code: string; customer_id: number; customer_name: string; customer_phone: string;
  asset_type: string; brand: string; model: string; serial_number: string; issue: string; diagnosis: string;
  status: TicketStatus; priority: Priority; assigned_to: string; estimated_at: string | null;
  labor_cents: number; parts_cents: number; paid_cents: number; notes: string; created_at: string; updated_at: string;
}
export interface DashboardData {
  active: number; ready: number; urgent: number; delivered_today: number; revenue_cents: number;
  status_counts: Record<TicketStatus, number>; recent: Ticket[];
}
export interface Business { name: string; phone: string; address: string; currency: string; accent: string; accent_secondary: string; ticket_prefix: string }

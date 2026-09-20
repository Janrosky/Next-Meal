export type Role = 'admin' | 'cashier' | 'kitchen';
export type User = { id: number; username: string; role: Role; active?: boolean };
export type Business = {
  name: string; tagline: string; sinpe_phone: string; phone: string; address: string;
  logo_url: string; cover_url: string; primary_color: string; accent_color: string;
  background_color: string; surface_color: string; text_color: string;
  hero_title: string; receipt_footer: string; opening_hours: string;
  accepting_orders: boolean; closed_message: string;
};
export type FiscalProfile = {
  legal_name: string; identification: string; activity_code: string;
  email: string; branch_code: string; terminal_code: string;
};
export type Backup = { filename: string; size: number; created_at: number };
export type Category = { id: number; name: string; sort_order: number };
export type Product = {
  id: number; name: string; description: string; category_id: number;
  price_cents: number; available: boolean; icon: string;
  image_url: string; featured: boolean; sort_order: number; allergens: string; cabys: string;
};
export type Catalog = { categories: Category[]; products: Product[] };
export type OrderStatus = 'awaiting_payment' | 'queued' | 'preparing' | 'ready' | 'delivered' | 'cancelled';
export type PaymentMethod = 'cash' | 'card' | 'sinpe';
export type Order = {
  id: number; number: string; created_at: number; updated_at: number;
  status: OrderStatus; payment_status: 'unpaid' | 'paid'; total_cents: number;
  service_mode: 'dine_in' | 'takeaway'; table_number: string; notes: string;
  items: { product_id: number; name: string; quantity: number; unit_price_cents: number }[];
  payment: null | { method: PaymentMethod; amount_cents: number; received_cents: number; change_cents: number; reference: string };
};
export type OrderDraft = {
  request_key: string; items: { product_id: number; quantity: number }[];
  notes: string; service_mode: 'dine_in' | 'takeaway'; table_number: string;
};
export type Shift = {
  id: number; opened_at: number; closed_at: number | null; opening_cents: number;
  cash_sales_cents: number; expected_cents: number; counted_cents: number | null;
  difference_cents: number | null; notes: string;
  movement_total_cents: number;
  movements: { id: number; kind: 'deposit' | 'withdrawal' | 'expense'; amount_cents: number;
    reason: string; created_at: number; user_id: number }[];
};
export type Shifts = { current: Shift | null; history: Shift[] };
export type Report = {
  day: string; total_cents: number; orders_paid: number; kitchen_pending: number;
  by_method: Record<PaymentMethod, number>;
  top_products: { name: string; quantity: number; total_cents: number }[];
};
export type Audit = {
  id: number; username: string; action: string; entity_id: string;
  created_at: number; details: string;
};

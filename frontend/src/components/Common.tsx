import type { ReactNode } from 'react';
import { AlertCircle, ChefHat, LoaderCircle } from 'lucide-react';
import type { Order } from '../types';
import { money, statusLabel } from '../lib/format';
import { useBusiness } from '../lib/theme';

export function Brand({ name, compact = false }: { name?: string; compact?: boolean }) {
  const business = useBusiness();
  return <div className="brand">{business.logo_url
    ? <img className="brand-logo" src={business.logo_url} alt={'Logo de ' + business.name} />
    : <span className="brand-mark"><ChefHat size={25} /></span>}
    <div><strong>{name ?? business.name}</strong>{!compact && <small>{business.tagline}</small>}</div></div>;
}
export function Notice({ error, message }: { error?: string; message?: string }) {
  return <>{error && <div className="notice error" role="alert"><AlertCircle size={18} />{error}</div>}
    {message && <div className="notice success" role="status">{message}</div>}</>;
}
export function Loading() { return <div className="empty"><LoaderCircle className="spin" /> Cargando…</div>; }
export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty"><ChefHat size={34} /><p>{children}</p></div>;
}
export function Status({ order }: { order: Order }) {
  return <span className={'badge status-' + order.status}>{statusLabel[order.status]}</span>;
}
export function OrderLines({ order, prices = true }: { order: Order; prices?: boolean }) {
  return <><div className="order-lines">{order.items.map(item =>
    <div className="order-line" key={item.product_id}><span className="quantity">{item.quantity}</span>
      <span>{item.name}</span>{prices && <strong>{money(item.quantity * item.unit_price_cents)}</strong>}</div>)}</div>
    <div className="order-context">{order.service_mode === 'dine_in' ? 'Para comer aquí' : 'Para llevar'}
      {order.table_number && ' · Mesa ' + order.table_number}</div>
    {order.notes && <div className="kitchen-note"><strong>Nota:</strong> {order.notes}</div>}</>;
}

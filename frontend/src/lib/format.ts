import type { OrderStatus, PaymentMethod, Role } from '../types';

export const money = (cents: number) =>
  new Intl.NumberFormat('es-CR', { style: 'currency', currency: 'CRC', maximumFractionDigits: 2 }).format(cents / 100);

export function parseMoney(value: string): number {
  if (!/^\d+(\.\d{1,2})?$/.test(value)) throw new Error('Ingresá un monto válido, con hasta dos decimales.');
  const [whole, fraction = ''] = value.split('.');
  const cents = Number(whole) * 100 + Number(fraction.padEnd(2, '0'));
  if (!Number.isSafeInteger(cents) || cents > 100_000_000) throw new Error('El monto es demasiado alto.');
  return cents;
}

export const dateTime = (seconds: number) =>
  new Intl.DateTimeFormat('es-CR', { timeZone: 'America/Costa_Rica', dateStyle: 'short', timeStyle: 'short' }).format(new Date(seconds * 1000));

export const today = () => new Intl.DateTimeFormat('en-CA', {
  timeZone: 'America/Costa_Rica', year: 'numeric', month: '2-digit', day: '2-digit',
}).format(new Date());

export const statusLabel: Record<OrderStatus, string> = {
  awaiting_payment: 'Por cobrar', queued: 'En espera', preparing: 'En preparación',
  ready: 'Listo', delivered: 'Entregado', cancelled: 'Cancelado',
};
export const methodLabel: Record<PaymentMethod, string> = { cash: 'Efectivo', card: 'Tarjeta', sinpe: 'SINPE Móvil' };
export const roleLabel: Record<Role, string> = { admin: 'Administrador', cashier: 'Caja', kitchen: 'Cocina' };


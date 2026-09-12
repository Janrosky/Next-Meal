import { useRef, useState } from 'react';
import { Banknote, CreditCard, Smartphone, Search, CheckCircle2 } from 'lucide-react';
import { Empty, Loading, Notice, OrderLines, Status } from '../components/Common';
import { ApiError, newKey, post } from '../lib/api';
import { dateTime, methodLabel, money, parseMoney } from '../lib/format';
import { useAction, useResource } from '../lib/hooks';
import type { Business, Order, PaymentMethod, Shifts } from '../types';

function PaymentForm({ order, hasShift, sinpe }: { order: Order; hasShift: boolean; sinpe: string }) {
  const [method, setMethod] = useState<PaymentMethod>('cash');
  const [received, setReceived] = useState('');
  const [reference, setReference] = useState('');
  const [paid, setPaid] = useState<Order | null>(null);
  const [reason, setReason] = useState('');
  const [cancelling, setCancelling] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const pending = useRef<object | null>(null);
  const action = useAction();
  const parsed = /^\d+(\.\d{1,2})?$/.test(received) ? Math.round(Number(received) * 100) : 0;

  async function pay() {
    await action.run(async () => {
      const payload = pending.current ?? {
        request_key: newKey(), method, reference,
        received_cents: method === 'cash' ? parseMoney(received) : null,
      };
      pending.current = payload;
      setUncertain(true);
      try {
        const result = await post<Order>('/staff/orders/' + order.id + '/pay', payload);
        setPaid(result); pending.current = null; setUncertain(false);
      } catch (error) {
        if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
          pending.current = null; setUncertain(false);
        }
        throw error;
      }
    });
  }

  return <section className="panel payment-panel"><div className="row-between"><h2>Pedido #{order.number}</h2><Status order={paid ?? order} /></div>
    <p className="muted small">{dateTime(order.created_at)}</p><OrderLines order={order} />
    <div className="cart-total"><span>Total a cobrar</span><strong>{money(order.total_cents)}</strong></div>
    {paid ? <div className="notice success"><CheckCircle2 size={24} /><div><strong>Pago registrado. Ya está en cocina.</strong><p>Vuelto: {money(paid.payment?.change_cents ?? 0)}</p></div></div>
      : order.payment_status === 'paid' ? <div className="notice success">Pagado con {methodLabel[order.payment!.method]}. Vuelto: {money(order.payment!.change_cents)}</div>
      : order.status === 'cancelled' ? <div className="notice">Pedido cancelado.</div> : <>
        {!hasShift && <div className="notice error">Abrí la caja en «Turno de caja» para cobrar.</div>}
        <div className="payment-methods">{([
          ['cash', Banknote], ['card', CreditCard], ['sinpe', Smartphone],
        ] as const).map(([key, Icon]) => <button key={key} disabled={uncertain || action.busy} className={method === key ? 'selected' : ''} onClick={() => setMethod(key)}><Icon size={21} />{methodLabel[key]}</button>)}</div>
        {method === 'cash' ? <><label>Efectivo recibido (₡)<input type="number" min={order.total_cents / 100} step="0.01" value={received} disabled={uncertain} onChange={e => setReceived(e.target.value)} /></label><div className="change-box">Vuelto <strong>{money(Math.max(0, parsed - order.total_cents))}</strong></div></>
          : <><p className="notice">{method === 'sinpe' && sinpe ? 'SINPE del negocio: ' + sinpe + '. ' : ''}Confirmá la recepción del pago antes de registrarlo.</p><label>Referencia (opcional)<input maxLength={100} value={reference} disabled={uncertain} onChange={e => setReference(e.target.value)} /></label></>}
        <button className="primary wide" disabled={action.busy || !hasShift || (!uncertain && method === 'cash' && parsed < order.total_cents)} onClick={() => void pay()}>{action.busy ? 'Registrando…' : uncertain ? 'Reintentar el mismo pago' : 'Confirmar pago y enviar a cocina'}</button>
        {uncertain && <p className="small muted">Si la conexión falló, reintentá el mismo pago. No vuelvas a cobrar al cliente.</p>}
        {!uncertain && <button className="text-button danger" onClick={() => setCancelling(!cancelling)}>Cancelar pedido sin pagar</button>}
        {cancelling && <form onSubmit={e => { e.preventDefault(); void action.run(() => post('/staff/orders/' + order.id + '/cancel', { reason }), 'Pedido cancelado.'); }}>
          <label>Motivo<input minLength={3} maxLength={300} required value={reason} onChange={e => setReason(e.target.value)} /></label><button className="secondary" disabled={action.busy}>Confirmar cancelación</button></form>}
      </>}
    <Notice error={action.error} message={action.message} />
  </section>;
}

export default function Cashier() {
  const orders = useResource<Order[]>('/staff/orders');
  const shifts = useResource<Shifts>('/staff/shifts');
  const business = useResource<Business>('/business');
  const [selected, setSelected] = useState<number | null>(null);
  const [search, setSearch] = useState('');
  const [showPaid, setShowPaid] = useState(false);
  const selectedOrder = orders.data?.find(o => o.id === selected);
  const visible = orders.data?.filter(o => (showPaid || o.payment_status === 'unpaid') && o.number.includes(search)) ?? [];
  return <><div className="page-heading"><div><p className="eyebrow">CADA PEDIDO CUENTA</p><h1>Caja</h1><p>Confirmá el pago y el equipo de cocina se encarga del resto.</p></div><span className={'badge ' + (shifts.data?.current ? 'status-ready' : 'status-awaiting_payment')}>{shifts.data?.current ? 'Caja abierta' : 'Caja cerrada'}</span></div>
    <Notice error={orders.error || shifts.error} />
    <div className="cashier-layout"><section><div className="list-toolbar"><label className="search"><Search size={18} /><input placeholder="Número de pedido…" value={search} onChange={e => setSearch(e.target.value)} /></label><label className="check-label"><input type="checkbox" checked={showPaid} onChange={e => setShowPaid(e.target.checked)} /> Ver pagados</label></div>
      {!orders.data ? <Loading /> : !visible.length ? <Empty>No hay pedidos por cobrar. Los nuevos aparecerán aquí.</Empty> : <div className="order-list">{visible.map(o =>
        <button key={o.id} className={'order-summary ' + (selected === o.id ? 'selected' : '')} onClick={() => setSelected(o.id)}>
          <div><strong>#{o.number}</strong><Status order={o} /></div><p>{o.items.map(i => i.quantity + ' × ' + i.name).join(', ')}</p><div><small>{dateTime(o.created_at)}</small><strong>{money(o.total_cents)}</strong></div>
        </button>)}</div>}</section>
      {selectedOrder ? <PaymentForm key={selectedOrder.id} order={selectedOrder} hasShift={!!shifts.data?.current} sinpe={business.data?.sinpe_phone ?? ''} /> : <section className="panel"><Empty>Seleccioná un pedido para cobrar.</Empty></section>}
    </div></>;
}


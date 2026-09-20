import { useState } from 'react';
import { createPortal } from 'react-dom';
import { useBusiness } from '../lib/theme';
import { dateTime, methodLabel, money } from '../lib/format';
import type { Order } from '../types';

export default function PrintReceipt({ order }: { order: Order }) {
  const business = useBusiness();
  const [printing, setPrinting] = useState(false);
  return <><button type="button" className="secondary" onClick={() => {
    setPrinting(true);
    requestAnimationFrame(() => requestAnimationFrame(() => {
      window.print();
      setPrinting(false);
    }));
  }}>Imprimir recibo</button>
    {printing && createPortal(<section className="print-receipt">
      <h2>{business.name}</h2><p>{business.address}<br />{business.phone}</p>
      <h3>Pedido #{order.number}</h3><p>{dateTime(order.created_at)}</p>
      <p>{order.payment_status === 'paid' ? 'PAGADO' : 'PENDIENTE DE PAGO'}</p>
      <p>{order.service_mode === 'dine_in' ? 'Comer aquí' : 'Para llevar'} {order.table_number && '· Mesa ' + order.table_number}</p>
      {order.items.map(item => <div className="receipt-line" key={item.product_id}>
        <span>{item.quantity} × {item.name}</span><strong>{money(item.quantity * item.unit_price_cents)}</strong>
      </div>)}
      <hr /><div className="receipt-line"><strong>Total</strong><strong>{money(order.total_cents)}</strong></div>
      {order.payment && <p>{methodLabel[order.payment.method]}<br />Recibido: {money(order.payment.received_cents)}<br />Vuelto: {money(order.payment.change_cents)}</p>}
      {order.notes && <p>Nota: {order.notes}</p>}
      <p>{business.receipt_footer}</p><small>Recibo de pedido. No es un comprobante electrónico tributario.</small>
    </section>, document.body)}
  </>;
}

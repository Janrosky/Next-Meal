import { useState } from 'react';
import { Notice, OrderLines, Status } from '../components/Common';
import { dateTime, methodLabel, money } from '../lib/format';
import { useResource } from '../lib/hooks';
import type { Audit, Order } from '../types';
import PrintReceipt from '../components/PrintReceipt';

const actions: Record<string, string> = {
  'order.created': 'Pedido creado', 'order.paid': 'Pago registrado', 'order.status': 'Estado de cocina',
  'order.cancelled': 'Pedido cancelado', 'product.saved': 'Producto guardado',
  'category.saved': 'Categoría guardada', 'user.created': 'Empleado creado',
  'user.updated': 'Empleado actualizado', 'shift.opened': 'Caja abierta',
  'shift.closed': 'Caja cerrada', 'business.updated': 'Negocio actualizado',
  'cash.movement': 'Movimiento de efectivo', 'fiscal.updated': 'Datos fiscales actualizados',
};

export default function History() {
  const orders = useResource<Order[]>('/staff/orders?history=true', 30000);
  const audit = useResource<Audit[]>('/admin/audit', 30000);
  const [tab, setTab] = useState('orders');
  return <><div className="page-heading"><div><p className="eyebrow">CADA MOVIMIENTO TIENE HISTORIA</p><h1>Historial</h1><p>Últimos 300 pedidos y 200 movimientos del negocio.</p></div></div>
    <div className="categories"><button className={tab === 'orders' ? 'selected' : ''} onClick={() => setTab('orders')}>Pedidos</button><button className={tab === 'audit' ? 'selected' : ''} onClick={() => setTab('audit')}>Actividad</button></div>
    <Notice error={orders.error || audit.error} />
    <section className="panel">{tab === 'orders' ? orders.data?.map(order => <details className="history-order" key={order.id}><summary><strong>#{order.number}</strong><span>{dateTime(order.created_at)}</span><Status order={order} /><strong>{money(order.total_cents)}</strong></summary><OrderLines order={order} />{order.payment && <p className="small">Pagado con {methodLabel[order.payment.method]} · Vuelto {money(order.payment.change_cents)}</p>}<PrintReceipt order={order} /></details>)
      : <div className="table-scroll"><table><thead><tr><th>Fecha</th><th>Empleado</th><th>Acción</th><th>Registro</th></tr></thead><tbody>{audit.data?.map(event => <tr key={event.id}><td>{dateTime(event.created_at)}</td><td>{event.username}</td><td>{actions[event.action] ?? event.action}</td><td>#{event.entity_id}</td></tr>)}</tbody></table></div>}
    </section></>;
}

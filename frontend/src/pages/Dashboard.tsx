import { useState } from 'react';
import { Banknote, Download, ShoppingBag, TrendingUp, Utensils } from 'lucide-react';
import { Empty, Notice } from '../components/Common';
import { downloadSales } from '../lib/api';
import { methodLabel, money, today } from '../lib/format';
import { useAction, useResource } from '../lib/hooks';
import type { PaymentMethod, Report } from '../types';

export default function Dashboard() {
  const [day, setDay] = useState(today);
  const report = useResource<Report>('/admin/report?day=' + day);
  const action = useAction();
  const data = report.data;
  return <><div className="page-heading"><div><p className="eyebrow">TU NEGOCIO, DE UN VISTAZO</p><h1>Así va tu local</h1><p>Ventas cobradas del día, en horario de Costa Rica.</p></div><div className="inline-actions"><label className="visually-hidden" htmlFor="report-day">Fecha del reporte</label><input id="report-day" type="date" value={day} onChange={e => { if (e.target.value) setDay(e.target.value); }} /><button className="secondary" disabled={action.busy} onClick={() => void action.run(() => downloadSales(day))}><Download size={17} /> Exportar</button></div></div>
    <Notice error={report.error || action.error} />
    <div className="metrics">{[
      ['Ventas cobradas', money(data?.total_cents ?? 0), Banknote],
      ['Pedidos pagados', String(data?.orders_paid ?? 0), ShoppingBag],
      ['Ticket promedio', money(data?.orders_paid ? Math.round(data.total_cents / data.orders_paid) : 0), TrendingUp],
      ['En cocina ahora', String(data?.kitchen_pending ?? 0), Utensils],
    ].map(([label, value, Icon]) => {
      const MetricIcon = Icon as typeof Banknote;
      return <article className="metric" key={String(label)}><div className="row-between"><span>{String(label)}</span><MetricIcon size={20} /></div><strong>{String(value)}</strong></article>;
    })}</div>
    <div className="two-columns"><section className="panel"><p className="eyebrow">CÓMO TE PAGAN</p><h2>Ventas por medio de pago</h2><div className="method-report">{(['cash', 'card', 'sinpe'] as PaymentMethod[]).map(method => <div key={method}><div className="row-between"><span>{methodLabel[method]}</span><strong>{money(data?.by_method[method] ?? 0)}</strong></div><progress max={data?.total_cents || 1} value={data?.by_method[method] ?? 0} /></div>)}</div></section>
    <section className="panel"><p className="eyebrow">LOS FAVORITOS DEL DÍA</p><h2>Productos más vendidos</h2>{!data?.top_products.length ? <Empty>Las primeras ventas aparecerán aquí.</Empty> : data.top_products.map((product, index) => <div className="top-product" key={product.name}><span className="rank">{index + 1}</span><div><strong>{product.name}</strong><small>{product.quantity} unidades</small></div><strong>{money(product.total_cents)}</strong></div>)}</section></div>
  </>;
}


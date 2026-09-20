import { useState } from 'react';
import { Banknote } from 'lucide-react';
import { Empty, Notice } from '../components/Common';
import { post } from '../lib/api';
import { dateTime, money, parseMoney } from '../lib/format';
import { useAction, useResource } from '../lib/hooks';
import type { Shifts as ShiftsData } from '../types';
import CashMovements from '../components/CashMovements';

export default function Shifts() {
  const resource = useResource<ShiftsData>('/staff/shifts');
  const action = useAction();
  const [amount, setAmount] = useState('');
  const [notes, setNotes] = useState('');
  const current = resource.data?.current;
  return <><div className="page-heading"><div><p className="eyebrow">LAS CUENTAS CLARAS</p><h1>Turno de caja</h1><p>Una caja compartida por local. Registrá el fondo inicial y el efectivo al cierre.</p></div></div>
    <Notice error={resource.error || action.error} message={action.message} />
    <div className="two-columns"><section className="panel"><div className="section-title"><Banknote /><h2>{current ? 'Caja abierta · #' + current.id : 'Abrir una nueva caja'}</h2></div>
      {current && <><p className="muted">Abierta {dateTime(current.opened_at)}</p><dl className="totals"><div><dt>Fondo inicial</dt><dd>{money(current.opening_cents)}</dd></div><div><dt>Ventas en efectivo</dt><dd>{money(current.cash_sales_cents)}</dd></div><div><dt>Movimientos netos</dt><dd>{money(current.movement_total_cents)}</dd></div><div><dt>Efectivo esperado</dt><dd>{money(current.expected_cents)}</dd></div></dl></>}
      <form onSubmit={e => { e.preventDefault(); void action.run(async () => {
        const cents = parseMoney(amount);
        if (current) await post('/staff/shifts/' + current.id + '/close', { counted_cents: cents, notes });
        else await post('/staff/shifts', { opening_cents: cents });
        setAmount(''); setNotes('');
      }, current ? 'Caja cerrada. El resultado está en el historial.' : 'Caja abierta. Ya podés cobrar.'); }}>
        <label>{current ? 'Efectivo contado al cierre (₡)' : 'Fondo inicial en efectivo (₡)'}<input type="number" min="0" step="0.01" required value={amount} onChange={e => setAmount(e.target.value)} /></label>
        {current && <label>Observaciones del cierre<textarea maxLength={300} value={notes} onChange={e => setNotes(e.target.value)} placeholder="Explicá cualquier diferencia de efectivo." /></label>}
        <button className="primary" disabled={action.busy || !resource.data || !!resource.error}>{current ? 'Confirmar cierre de caja' : 'Abrir caja'}</button>
      </form><p className="small muted">El esperado incluye el fondo inicial, ventas en efectivo y movimientos registrados. Las devoluciones de ventas aún no están habilitadas.</p>
    </section><section className="panel"><h2>Últimos cierres</h2>{!resource.data?.history.length ? <Empty>Todavía no hay cierres.</Empty> : <div className="shift-history">{resource.data.history.map(shift => <article key={shift.id}><div className="row-between"><strong>Caja #{shift.id}</strong><span className={'badge ' + (shift.difference_cents === 0 ? 'status-ready' : 'status-awaiting_payment')}>{shift.difference_cents === 0 ? 'Cuadra' : 'Con diferencia'}</span></div><p className="muted small">{dateTime(shift.closed_at!)}</p><div className="row-between"><span>Contado: {money(shift.counted_cents!)}</span><strong>Diferencia: {money(shift.difference_cents!)}</strong></div><p className="small">Movimientos netos: {money(shift.movement_total_cents)}</p>{shift.movements.length > 0 && <details><summary>Ver movimientos</summary>{shift.movements.map(m => <p className="small" key={m.id}>{m.kind === 'deposit' ? 'Entrada' : m.kind === 'expense' ? 'Gasto' : 'Retiro'}: {money(m.amount_cents)} · {m.reason}</p>)}</details>}{shift.notes && <p className="small">{shift.notes}</p>}</article>)}</div>}</section></div>
    {current && <CashMovements key={current.id} shift={current} />}</>;
}

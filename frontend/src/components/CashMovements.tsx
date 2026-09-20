import { useRef, useState } from 'react';
import { Notice } from './Common';
import { ApiError, newKey, post } from '../lib/api';
import { useAction } from '../lib/hooks';
import { dateTime, money, parseMoney } from '../lib/format';
import type { Shift } from '../types';

const names = { deposit: 'Entrada de efectivo', withdrawal: 'Retiro', expense: 'Gasto' };
type Draft = { request_key: string; kind: keyof typeof names; amount_cents: number; reason: string };

export default function CashMovements({ shift }: { shift: Shift }) {
  const [kind, setKind] = useState<keyof typeof names>('expense');
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const [uncertain, setUncertain] = useState(false);
  const pending = useRef<Draft | null>(null);
  const action = useAction();
  return <section className="panel cash-movements"><h2>Movimientos de efectivo</h2>
    <p className="small muted">Entradas, retiros y gastos ajustan el saldo de caja. No modifican las ventas registradas.</p>
    <form onSubmit={e => {
      e.preventDefault();
      void action.run(async () => {
        const draft = pending.current ?? { request_key: newKey(), kind, amount_cents: parseMoney(amount), reason };
        pending.current = draft; setUncertain(true);
        try {
          await post('/staff/shifts/' + shift.id + '/movements', draft);
          pending.current = null; setUncertain(false); setAmount(''); setReason('');
        } catch (error) {
          if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
            pending.current = null; setUncertain(false);
          }
          throw error;
        }
      }, 'Movimiento registrado.');
    }}>
      <label>Tipo de movimiento<select value={kind} disabled={uncertain} onChange={e => setKind(e.target.value as keyof typeof names)}>
        {Object.entries(names).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
      </select></label>
      <label>Monto del movimiento (₡)<input type="number" required min="0.01" step="0.01" value={amount} disabled={uncertain} onChange={e => setAmount(e.target.value)} /></label>
      <label>Motivo del movimiento<input required minLength={3} maxLength={200} value={reason} disabled={uncertain} onChange={e => setReason(e.target.value)} /></label>
      <Notice error={action.error} message={action.message} />
      {uncertain && <p className="notice">Reintentá el mismo movimiento para confirmar su resultado sin duplicarlo.</p>}
      <button className="secondary" disabled={action.busy}>{uncertain ? 'Reintentar movimiento' : 'Registrar movimiento'}</button>
    </form>
    <div className="movement-list">{shift.movements.map(m => <article key={m.id}><div className="row-between"><strong>{names[m.kind]}</strong><strong>{m.kind === 'deposit' ? '+' : '−'}{money(m.amount_cents)}</strong></div><p>{m.reason}</p><small>{dateTime(m.created_at)}</small></article>)}</div>
  </section>;
}

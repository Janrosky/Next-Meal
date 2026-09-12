import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Volume2 } from 'lucide-react';
import { Empty, Notice, OrderLines } from '../components/Common';
import { post } from '../lib/api';
import { useAction, useResource } from '../lib/hooks';
import type { Order, OrderStatus } from '../types';

const columns: { status: OrderStatus; title: string; next: OrderStatus; action: string }[] = [
  { status: 'queued', title: 'En espera', next: 'preparing', action: 'Comenzar' },
  { status: 'preparing', title: 'En preparación', next: 'ready', action: 'Marcar listo' },
  { status: 'ready', title: 'Listos para salir', next: 'delivered', action: 'Entregado' },
];

export default function Kitchen() {
  const orders = useResource<Order[]>('/staff/orders');
  const action = useAction();
  const [sound, setSound] = useState(false);
  const audio = useRef<AudioContext | null>(null);
  const known = useRef<Set<number> | null>(null);
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30000);
    return () => window.clearInterval(timer);
  }, []);
  useEffect(() => {
    if (!orders.data) return;
    const ids = new Set(orders.data.filter(o => o.payment_status === 'paid').map(o => o.id));
    if (sound && known.current && [...ids].some(id => !known.current!.has(id)) && audio.current) {
      const oscillator = audio.current.createOscillator();
      const gain = audio.current.createGain();
      oscillator.connect(gain); gain.connect(audio.current.destination);
      oscillator.frequency.value = 740; gain.gain.value = 0.08;
      oscillator.start(); oscillator.stop(audio.current.currentTime + 0.3);
    }
    known.current = ids;
  }, [orders.data, sound]);
  useEffect(() => () => { void audio.current?.close(); }, []);
  const active = orders.data?.filter(o => o.payment_status === 'paid') ?? [];
  return <><div className="page-heading"><div><p className="eyebrow">EL CORAZÓN DEL LOCAL</p><h1>Cocina</h1><p>Pedidos pagados, en orden de llegada.</p></div><button className={'secondary ' + (sound ? 'selected' : '')} onClick={() => {
    if (!audio.current) audio.current = new AudioContext();
    void audio.current.resume(); setSound(!sound);
  }}><Volume2 size={18} /> {sound ? 'Sonido activado' : 'Activar sonido'}</button></div>
    <Notice error={orders.error || action.error} />
    <div className="kitchen-board">{columns.map(column => {
      const queue = active.filter(o => o.status === column.status).sort((a, b) => a.id - b.id);
      return <section className={'kitchen-column column-' + column.status} key={column.status}>
        <div className="column-heading"><h2>{column.title}</h2><span className="count">{queue.length}</span></div>
        {!queue.length && <Empty>Todo al día por aquí.</Empty>}
        {queue.map(order => <article className="kitchen-ticket" key={order.id}>
          <div className="row-between"><h2>#{order.number}</h2><span className={'age ' + (now / 1000 - order.created_at > 900 ? 'late' : '')}>{Math.max(0, Math.floor((now / 1000 - order.created_at) / 60))} min</span></div>
          <OrderLines order={order} prices={false} />
          <button className="primary wide" disabled={action.busy || !!orders.error} onClick={() => void action.run(() => post('/staff/orders/' + order.id + '/status', { status: column.next }))}>{column.action}<ArrowRight size={16} /></button>
        </article>)}</section>;
    })}</div></>;
}


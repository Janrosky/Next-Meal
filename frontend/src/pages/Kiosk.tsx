import { useEffect, useRef, useState } from 'react';
import { ArrowRight, Check, Minus, Plus, Search, ShoppingBag, Trash2 } from 'lucide-react';
import { Brand, Empty, Loading, Notice } from '../components/Common';
import { ApiError, newKey, post } from '../lib/api';
import { money } from '../lib/format';
import { useAction, useResource } from '../lib/hooks';
import type { Business, Catalog, Order, OrderDraft } from '../types';
import PrintReceipt from '../components/PrintReceipt';

const PENDING_KEY = 'sodalocal.pending-order';
function readPending(): OrderDraft | null {
  try { return JSON.parse(sessionStorage.getItem(PENDING_KEY) || 'null'); }
  catch { sessionStorage.removeItem(PENDING_KEY); return null; }
}

export default function Kiosk() {
  const catalog = useResource<Catalog>('/catalog', 30000);
  const business = useResource<Business>('/business', 60000);
  const [category, setCategory] = useState(0);
  const [search, setSearch] = useState('');
  const [cart, setCart] = useState<Record<number, number>>({});
  const [notes, setNotes] = useState('');
  const [mode, setMode] = useState<'dine_in' | 'takeaway'>('takeaway');
  const [table, setTable] = useState('');
  const [pending, setPending] = useState<OrderDraft | null>(readPending);
  const [receipt, setReceipt] = useState<Order | null>(null);
  const action = useAction();
  const receiptRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => { if (receipt) receiptRef.current?.focus(); }, [receipt]);
  const products = catalog.data?.products ?? [];
  const items = products.filter(p => cart[p.id]);
  const missingProducts = Object.keys(cart).some(id => !products.some(p => p.id === Number(id)));
  const total = items.reduce((sum, p) => sum + p.price_cents * cart[p.id], 0);
  const count = Object.values(cart).reduce((sum, q) => sum + q, 0);
  const visible = products.filter(p => (!category || p.category_id === category) &&
    (p.name + ' ' + p.description).toLocaleLowerCase().includes(search.toLocaleLowerCase()));

  function quantity(id: number, change: number) {
    if (pending || action.busy) return;
    setCart(previous => {
      const next = { ...previous };
      next[id] = Math.min(50, Math.max(0, (next[id] || 0) + change));
      if (!next[id]) delete next[id];
      return next;
    });
  }
  async function confirm() {
    const draft: OrderDraft = pending ?? {
      request_key: newKey(), items: items.map(p => ({ product_id: p.id, quantity: cart[p.id] })),
      notes, service_mode: mode, table_number: mode === 'dine_in' ? table : '',
    };
    setPending(draft);
    sessionStorage.setItem(PENDING_KEY, JSON.stringify(draft));
    await action.run(async () => {
      try {
        const order = await post<Order>('/orders', draft);
        setReceipt(order); setCart({}); setNotes(''); setTable('');
        setPending(null); sessionStorage.removeItem(PENDING_KEY);
      } catch (error) {
        if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
          setPending(null); sessionStorage.removeItem(PENDING_KEY);
          void catalog.reload();
        }
        throw error;
      }
    });
  }

  return <div className="kiosk">
    <header className="kiosk-header"><Brand name={business.data?.name ?? 'Mi Soda'} />
      <div className="header-right"><span className="local-pill"><span /> Pedí a tu gusto</span><a href="#/staff">Empleados ↗</a></div>
    </header>
    {receipt ? <main className="receipt">
      <div className="receipt-check"><Check size={42} /></div>
      <p className="eyebrow">¡YA RECIBIMOS TU PEDIDO!</p>
      <h1 ref={receiptRef} tabIndex={-1}>Pasá a caja a pagar.</h1>
      <p>Mostrá este número. Comenzaremos a preparar tu comida al confirmar el pago.</p>
      <div className="ticket-number"><small>TU PEDIDO</small><strong>#{receipt.number}</strong><span>{money(receipt.total_cents)}</span></div>
      <p>Efectivo · Tarjeta · SINPE Móvil</p>
      <div className="receipt-actions"><PrintReceipt order={receipt} /></div>
      <button className="primary" onClick={() => setReceipt(null)}>Hacer otro pedido <ArrowRight size={18} /></button>
    </main> : <div className="kiosk-layout"><main className="menu-main">
      <section className="menu-hero"><div><p className="eyebrow">CREA TU ORDEN</p>
        <h1>{business.data?.hero_title || 'Tu antojo, recién hecho.'}</h1>
        <p>{business.data?.tagline || 'Hecho aquí. Servido con cariño.'}</p>
        <span className="hero-steps">01 Elegí &nbsp; → &nbsp; 02 Ordená &nbsp; → &nbsp; 03 Pagá en caja</span></div>
        {business.data?.cover_url ? <img className="hero-cover" src={business.data.cover_url} alt={'Menú de ' + business.data.name} /> : <div className="hero-plate" aria-hidden="true"><span>🍛</span><div className="hero-stamp">SABOR<br />DE CASA</div></div>}
      </section>
      <div className="menu-toolbar"><h2>¿Qué se te antoja?</h2><label className="search"><Search size={18} /><input aria-label="Buscar en el menú" placeholder="Buscá tu favorito…" value={search} onChange={e => setSearch(e.target.value)} /></label></div>
      <nav className="categories" aria-label="Categorías"><button className={category === 0 ? 'selected' : ''} onClick={() => setCategory(0)}>Todo el menú</button>
        {catalog.data?.categories.map(c => <button key={c.id} className={category === c.id ? 'selected' : ''} onClick={() => setCategory(c.id)}>{c.name}</button>)}</nav>
      <Notice error={catalog.error || business.error} />
      {business.data && !business.data.accepting_orders && <p className="notice" role="status">{business.data.closed_message}</p>}
      {!catalog.data ? <Loading /> : visible.length === 0 ? <Empty>No hay productos para mostrar.</Empty> :
        <div className="product-grid">{visible.map(p => <article className="product-card" key={p.id}>
          <div className={'product-art art-' + (p.category_id % 4)}>{p.image_url ? <img src={p.image_url} alt={p.name} loading="lazy" /> : <span aria-hidden="true">{p.icon}</span>}{p.featured && <span className="featured-label">Favorito</span>}</div>
          <div className="product-copy"><h3>{p.name}</h3><p>{p.description}</p>
            {p.allergens && <details className="allergen-info"><summary>Información alimentaria</summary><p>{p.allergens}</p></details>}
            <div className="product-bottom"><strong>{money(p.price_cents)}</strong>
              <button className="add-button" disabled={!!pending || action.busy || (cart[p.id] ?? 0) >= 50} aria-label={'Agregar ' + p.name} onClick={() => quantity(p.id, 1)}><Plus size={21} /></button></div></div>
        </article>)}</div>}
      <p className="menu-footer">Preparado al momento · Precios finales en colones</p>
      <p className="menu-footer"><a href="/demo-photo-credits.html" target="_blank" rel="noreferrer">Fotografías ilustrativas · Créditos del menú de ejemplo</a></p>
      {business.data && <div className="business-contact"><p>{business.data.opening_hours}</p><p>{business.data.address}</p><p>{business.data.phone}</p></div>}
    </main><aside className="cart-panel"><div className="cart-heading"><ShoppingBag size={23} /><h2>Tu pedido</h2><span className="count">{count}</span></div>
      <p className="muted">Un buen momento empieza con buena comida.</p>
      <div className="segmented"><button disabled={!!pending} className={mode === 'takeaway' ? 'selected' : ''} onClick={() => setMode('takeaway')}>Para llevar</button>
        <button disabled={!!pending} className={mode === 'dine_in' ? 'selected' : ''} onClick={() => setMode('dine_in')}>Comer aquí</button></div>
      {mode === 'dine_in' && <label>Mesa (opcional)<input maxLength={12} value={table} disabled={!!pending} onChange={e => setTable(e.target.value)} /></label>}
      <div className="cart-items">{items.length === 0 && !pending ? <Empty>Agregá algo rico del menú.</Empty> : items.map(p =>
        <div className="cart-item" key={p.id}><span className="cart-icon">{p.image_url ? <img src={p.image_url} alt="" /> : p.icon}</span><div><strong>{p.name}</strong><small>{money(p.price_cents)}</small>
          <div className="stepper"><button disabled={!!pending} aria-label={'Quitar uno de ' + p.name} onClick={() => quantity(p.id, -1)}><Minus size={14} /></button><span>{cart[p.id]}</span><button disabled={!!pending || cart[p.id] >= 50} aria-label={'Sumar uno de ' + p.name} onClick={() => quantity(p.id, 1)}><Plus size={14} /></button></div></div>
          <strong>{money(p.price_cents * cart[p.id])}</strong></div>)}</div>
      {missingProducts && <div className="notice error">Un producto dejó de estar disponible. Vaciá el carrito y elegí de nuevo.</div>}
      {count > 0 && !pending && <button className="text-button" onClick={() => setCart({})}><Trash2 size={14} /> Vaciar carrito</button>}
      <label className="notes-label">¿Algo que debamos saber?<textarea placeholder="Ej.: sin cebolla, por favor." maxLength={300} value={notes} disabled={!!pending} onChange={e => setNotes(e.target.value)} /></label>
      <div className="cart-total"><span>Total</span><strong>{money(total)}</strong></div>
      <Notice error={action.error} />
      {pending && <p className="notice">Estamos confirmando tu pedido. Si se interrumpió la conexión, reintentá: conservaremos el mismo número.</p>}
      <button className="primary wide" disabled={action.busy || (!pending && (!count || missingProducts || !!catalog.error || !business.data?.accepting_orders))} onClick={() => void confirm()}>
        {action.busy ? 'Confirmando…' : pending ? 'Reintentar confirmación' : 'Confirmar pedido'} <ArrowRight size={19} /></button>
      <p className="cart-footnote">Pagás en caja al confirmar.<br />Efectivo, tarjeta o SINPE Móvil.</p>
    </aside></div>}
  </div>;
}

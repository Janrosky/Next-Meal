import { useEffect, useMemo, useState } from 'react';
import {
  Bell, Bike, CalendarDays, Car, Check, ChevronDown, CircleDollarSign, Clock3, Command,
  Computer, Gauge, Home, LayoutDashboard, Menu, PackageCheck, Palette, Plus, Search, Settings,
  Smartphone, Sparkles, TicketCheck, UserRound, UsersRound, WashingMachine, Wrench, X,
} from 'lucide-react';
import { api } from './api';
import type { Business, Customer, DashboardData, Priority, Ticket, TicketStatus } from './types';

const STATUS: Record<TicketStatus, { label: string; short: string; tone: string }> = {
  received: { label: 'Recibido', short: 'Recibido', tone: 'slate' },
  diagnosing: { label: 'En diagnóstico', short: 'Diagnóstico', tone: 'blue' },
  approval: { label: 'Esperando aprobación', short: 'Aprobación', tone: 'amber' },
  repairing: { label: 'En reparación', short: 'Reparación', tone: 'violet' },
  ready: { label: 'Listo para entregar', short: 'Listo', tone: 'green' },
  delivered: { label: 'Entregado', short: 'Entregado', tone: 'dark' },
};
const PRIORITY: Record<Priority, string> = { low: 'Baja', normal: 'Normal', high: 'Alta', urgent: 'Urgente' };
const ICONS: Record<string, typeof Wrench> = { Celular: Smartphone, Computadora: Computer, Automóvil: Car, Electrodoméstico: WashingMachine, Bicicleta: Bike };

function money(cents: number, currency = 'CRC') { return new Intl.NumberFormat('es-CR', { style: 'currency', currency, maximumFractionDigits: 0 }).format(cents / 100); }
function date(value: string | null) { return value ? new Intl.DateTimeFormat('es-CR', { day: '2-digit', month: 'short' }).format(new Date(value)) : 'Sin fecha'; }
function initials(name: string) { return name.split(' ').slice(0, 2).map(x => x[0]).join('').toUpperCase(); }

function StatusPill({ status }: { status: TicketStatus }) { const item = STATUS[status]; return <span className={`status-pill ${item.tone}`}><i />{item.label}</span>; }

function Shell({ children, page, setPage, business, onNew }: { children: React.ReactNode; page: string; setPage: (p: string) => void; business: Business; onNew: () => void }) {
  const [open, setOpen] = useState(false);
  const nav = [
    ['dashboard', 'Resumen', LayoutDashboard], ['tickets', 'Tickets', TicketCheck], ['customers', 'Clientes', UsersRound],
    ['inventory', 'Inventario', PackageCheck], ['settings', 'Personalización', Palette],
  ] as const;
  return <div className="shell" style={{ '--accent': business.accent, '--accent-2': business.accent_secondary } as React.CSSProperties}>
    <aside className={open ? 'sidebar open' : 'sidebar'}>
      <div className="brand"><span className="brand-mark"><Wrench size={18} /></span><div><strong>{business.name}</strong><small>Next-Fix workspace</small></div><button className="mobile-close" onClick={() => setOpen(false)}><X /></button></div>
      <p className="nav-label">OPERACIÓN</p>
      <nav>{nav.slice(0, 4).map(([id, label, Icon]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => { setPage(id); setOpen(false); }}><Icon size={19} />{label}{id === 'tickets' && <em>8</em>}</button>)}</nav>
      <p className="nav-label second">NEGOCIO</p>
      <nav>{nav.slice(4).map(([id, label, Icon]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => { setPage(id); setOpen(false); }}><Icon size={19} />{label}</button>)}</nav>
      <div className="sidebar-callout"><span><Sparkles size={16} /> Pro tip</span><p>Escaneá el QR del ticket para encontrar cualquier reparación en segundos.</p></div>
      <div className="profile"><span className="avatar">JR</span><div><strong>Administrador</strong><small>Sesión local</small></div><ChevronDown size={16} /></div>
    </aside>
    <div className="workspace">
      <header><button className="mobile-menu" onClick={() => setOpen(true)}><Menu /></button><div className="global-search"><Search size={18} /><input placeholder="Buscar ticket, cliente, serie o teléfono…" onFocus={() => setPage('tickets')} /><kbd><Command size={12} /> K</kbd></div><div className="header-actions"><button className="icon-button"><Bell size={19} /><i /></button><button className="primary" onClick={onNew}><Plus size={18} /> Nuevo ticket</button></div></header>
      <main>{children}</main>
    </div>
  </div>;
}

function Dashboard({ data, currency, goTickets, onNew }: { data: DashboardData | null; currency: string; goTickets: () => void; onNew: () => void }) {
  const stats = [
    ['Trabajos activos', data?.active ?? 0, 'En proceso ahora', Gauge, 'lime'],
    ['Listos para entregar', data?.ready ?? 0, 'Esperando al cliente', Check, 'green'],
    ['Prioridad urgente', data?.urgent ?? 0, 'Requieren atención', Clock3, 'orange'],
    ['Ingresos registrados', money(data?.revenue_cents ?? 0, currency), 'Total en tickets', CircleDollarSign, 'purple'],
  ] as const;
  return <>
    <div className="page-heading"><div><p className="eyebrow">LUNES, 21 DE SEPTIEMBRE</p><h1>Buenos días, <span>todo bajo control.</span></h1><p>Este es el pulso de tu taller hoy.</p></div><button className="secondary"><CalendarDays size={17} /> Esta semana <ChevronDown size={15} /></button></div>
    <section className="stat-grid">{stats.map(([label, value, hint, Icon, tone]) => <article className="stat-card" key={label}><div className={`stat-icon ${tone}`}><Icon /></div><div><p>{label}</p><strong>{value}</strong><small>{hint}</small></div></article>)}</section>
    <div className="dashboard-grid">
      <section className="panel flow-panel"><div className="panel-title"><div><h2>Flujo de trabajo</h2><p>Tickets activos por etapa</p></div><button onClick={goTickets}>Ver todos <span>→</span></button></div>
        <div className="flow-bars">{(['received', 'diagnosing', 'approval', 'repairing', 'ready'] as TicketStatus[]).map((status, i) => { const count = data?.status_counts?.[status] || 0; const total = Math.max(1, data?.active || 1); return <div className="flow-row" key={status}><span>{STATUS[status].short}</span><div><i style={{ width: `${Math.max(7, (count / total) * 100)}%`, animationDelay: `${i * 70}ms` }} /></div><strong>{count}</strong></div>; })}</div>
        <div className="flow-footer"><span><i className="pulse" /> Operación en vivo</span><b>{data?.active ?? 0} activos</b></div>
      </section>
      <section className="panel quick-panel"><div className="panel-title"><div><h2>Acciones rápidas</h2><p>Todo a un clic</p></div></div><div className="quick-grid">
        <button onClick={onNew}><span><Plus /></span><strong>Crear ticket</strong><small>Registrar un nuevo ingreso</small></button>
        <button onClick={goTickets}><span><Search /></span><strong>Buscar reparación</strong><small>Por cliente, código o serie</small></button>
        <button onClick={goTickets}><span><PackageCheck /></span><strong>Marcar entrega</strong><small>Cerrar un trabajo listo</small></button>
        <button><span><CircleDollarSign /></span><strong>Registrar pago</strong><small>Abono o pago completo</small></button>
      </div></section>
    </div>
    <section className="panel recent-panel"><div className="panel-title"><div><h2>Actividad reciente</h2><p>Últimos tickets actualizados</p></div><button onClick={goTickets}>Abrir bandeja →</button></div><TicketTable tickets={data?.recent || []} currency={currency} empty="Todavía no hay actividad." /></section>
  </>;
}

function TicketTable({ tickets, currency, onSelect, empty }: { tickets: Ticket[]; currency: string; onSelect?: (t: Ticket) => void; empty: string }) {
  return <div className="table-wrap"><table><thead><tr><th>Ticket</th><th>Cliente y equipo</th><th>Estado</th><th>Responsable</th><th>Entrega</th><th>Total</th></tr></thead><tbody>{tickets.map(ticket => { const Icon = ICONS[ticket.asset_type] || Wrench; return <tr key={ticket.id} onClick={() => onSelect?.(ticket)}><td><strong className="ticket-code">{ticket.code}</strong><small>{date(ticket.created_at)}</small></td><td><div className="asset-cell"><span><Icon /></span><div><strong>{ticket.customer_name}</strong><small>{ticket.brand} {ticket.model}</small></div></div></td><td><StatusPill status={ticket.status} /></td><td><span className="assignee">{initials(ticket.assigned_to || 'Sin asignar')}</span>{ticket.assigned_to || 'Sin asignar'}</td><td>{date(ticket.estimated_at)}</td><td><strong>{money(ticket.labor_cents + ticket.parts_cents, currency)}</strong></td></tr>; })}{!tickets.length && <tr><td colSpan={6} className="empty">{empty}</td></tr>}</tbody></table></div>;
}

function TicketsPage({ tickets, currency, onSelect, search, setSearch, status, setStatus }: { tickets: Ticket[]; currency: string; onSelect: (t: Ticket) => void; search: string; setSearch: (v: string) => void; status: string; setStatus: (v: string) => void }) {
  return <><div className="page-heading compact"><div><p className="eyebrow">CENTRO DE OPERACIONES</p><h1>Tickets de reparación</h1><p>Seguí cada trabajo desde la recepción hasta la entrega.</p></div></div><section className="panel tickets-panel"><div className="filters"><div className="field-search"><Search /><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por ticket, cliente, teléfono, marca o serie" /></div><select value={status} onChange={e => setStatus(e.target.value)}><option value="">Todos los estados</option>{Object.entries(STATUS).map(([value, item]) => <option value={value} key={value}>{item.label}</option>)}</select></div><TicketTable tickets={tickets} currency={currency} onSelect={onSelect} empty="No encontramos tickets con esos filtros." /></section></>;
}

function CustomersPage({ customers }: { customers: Customer[] }) { return <><div className="page-heading compact"><div><p className="eyebrow">RELACIONES</p><h1>Clientes</h1><p>Historial y datos de contacto en un solo lugar.</p></div></div><section className="customer-grid">{customers.map(c => <article className="customer-card" key={c.id}><span className="avatar large">{initials(c.name)}</span><div><h3>{c.name}</h3><p>{c.phone}</p><small>{c.email || 'Sin correo registrado'}</small></div><button><UserRound size={17} /> Ver perfil</button></article>)}</section></> }

function InventoryPage() { return <><div className="page-heading compact"><div><p className="eyebrow">REPUESTOS Y SUMINISTROS</p><h1>Inventario</h1><p>Una base preparada para controlar costos y disponibilidad.</p></div></div><section className="panel coming"><span><PackageCheck /></span><h2>Inventario inteligente, próxima etapa</h2><p>El núcleo ya contempla costos de repuestos por ticket. La siguiente versión añadirá existencias, mínimos, proveedores y movimientos auditados.</p><div><b>✓ Costos por reparación</b><b>Próximo · Alertas de mínimo</b><b>Próximo · Órdenes de compra</b></div></section></> }

function SettingsPage({ business, saved }: { business: Business; saved: (b: Business) => Promise<void> }) {
  const [form, setForm] = useState(business); const [ok, setOk] = useState(false);
  useEffect(() => setForm(business), [business]);
  return <><div className="page-heading compact"><div><p className="eyebrow">IDENTIDAD DEL NEGOCIO</p><h1>Personalización</h1><p>Hacé que Next-Fix se sienta completamente tuyo.</p></div></div><div className="settings-grid"><section className="panel form-panel"><h2>Información general</h2><label>Nombre del taller<input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></label><div className="two-cols"><label>Teléfono<input value={form.phone} onChange={e => setForm({ ...form, phone: e.target.value })} /></label><label>Prefijo de tickets<input value={form.ticket_prefix} maxLength={5} onChange={e => setForm({ ...form, ticket_prefix: e.target.value.toUpperCase() })} /></label></div><label>Dirección<input value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} /></label><h2 className="subhead">Colores de marca</h2><div className="color-row"><label>Principal<span><input type="color" value={form.accent} onChange={e => setForm({ ...form, accent: e.target.value })} />{form.accent}</span></label><label>Secundario<span><input type="color" value={form.accent_secondary} onChange={e => setForm({ ...form, accent_secondary: e.target.value })} />{form.accent_secondary}</span></label></div><button className="primary save" onClick={() => void saved(form).then(() => { setOk(true); setTimeout(() => setOk(false), 1800); })}>{ok ? <><Check /> Guardado</> : 'Guardar cambios'}</button></section><section className="theme-preview" style={{ background: `linear-gradient(145deg, ${form.accent}, ${form.accent_secondary})` }}><span>VISTA PREVIA</span><div><i><Wrench /></i><h2>{form.name || 'Mi taller'}</h2><p>{form.address || 'Tu dirección aparecerá aquí'}</p><button>Crear ticket</button></div></section></div></>;
}

function TicketDrawer({ ticket, currency, close, update }: { ticket: Ticket; currency: string; close: () => void; update: (t: Ticket) => void }) {
  const sequence = Object.keys(STATUS) as TicketStatus[];
  const setStatus = async (status: TicketStatus) => update(await api.setStatus(ticket.id, status));
  return <div className="overlay" onMouseDown={e => e.target === e.currentTarget && close()}><aside className="drawer"><div className="drawer-head"><div><p>{ticket.code}</p><h2>{ticket.brand} {ticket.model}</h2></div><button onClick={close}><X /></button></div><div className="drawer-body"><div className="drawer-customer"><span className="avatar large">{initials(ticket.customer_name)}</span><div><strong>{ticket.customer_name}</strong><p>{ticket.customer_phone}</p></div><StatusPill status={ticket.status} /></div><section><h3>Problema reportado</h3><p className="issue">{ticket.issue}</p></section><section><h3>Información del equipo</h3><dl><div><dt>Tipo</dt><dd>{ticket.asset_type}</dd></div><div><dt>Serie / placa</dt><dd>{ticket.serial_number || 'No registrada'}</dd></div><div><dt>Prioridad</dt><dd>{PRIORITY[ticket.priority]}</dd></div><div><dt>Responsable</dt><dd>{ticket.assigned_to || 'Sin asignar'}</dd></div></dl></section><section><h3>Actualizar etapa</h3><div className="status-options">{sequence.map(s => <button className={ticket.status === s ? 'selected' : ''} onClick={() => void setStatus(s)} key={s}><i />{STATUS[s].short}</button>)}</div></section><section className="totals"><div><span>Mano de obra</span><b>{money(ticket.labor_cents, currency)}</b></div><div><span>Repuestos</span><b>{money(ticket.parts_cents, currency)}</b></div><div className="grand"><span>Total</span><b>{money(ticket.labor_cents + ticket.parts_cents, currency)}</b></div><div><span>Pagado</span><b>{money(ticket.paid_cents, currency)}</b></div></section></div><div className="drawer-actions"><button className="secondary">Imprimir orden</button><button className="primary" onClick={() => void setStatus(ticket.status === 'ready' ? 'delivered' : 'ready')}>{ticket.status === 'ready' ? 'Confirmar entrega' : 'Marcar como listo'}</button></div></aside></div>;
}

function NewTicket({ customers, close, created }: { customers: Customer[]; close: () => void; created: (t: Ticket) => void }) {
  const [form, setForm] = useState({ customer_id: customers[0]?.id || 0, asset_type: 'Automóvil', brand: '', model: '', serial_number: '', issue: '', priority: 'normal' as Priority, assigned_to: '', labor_cents: 0, parts_cents: 0 });
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const submit = async (e: React.FormEvent) => { e.preventDefault(); setBusy(true); setError(''); try { created(await api.createTicket(form)); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } };
  return <div className="overlay modal-overlay"><form className="modal" onSubmit={submit}><div className="modal-head"><div><p>NUEVA RECEPCIÓN</p><h2>Crear ticket de reparación</h2></div><button type="button" onClick={close}><X /></button></div><div className="modal-body"><label>Cliente<select required value={form.customer_id} onChange={e => setForm({ ...form, customer_id: Number(e.target.value) })}><option value="">Seleccionar cliente</option>{customers.map(c => <option value={c.id} key={c.id}>{c.name} · {c.phone}</option>)}</select></label><div className="two-cols"><label>Tipo de equipo<select value={form.asset_type} onChange={e => setForm({ ...form, asset_type: e.target.value })}>{Object.keys(ICONS).map(x => <option key={x}>{x}</option>)}</select></label><label>Prioridad<select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value as Priority })}>{Object.entries(PRIORITY).map(([k, v]) => <option value={k} key={k}>{v}</option>)}</select></label></div><div className="two-cols"><label>Marca<input required placeholder="Ej. Toyota, Samsung" value={form.brand} onChange={e => setForm({ ...form, brand: e.target.value })} /></label><label>Modelo<input placeholder="Modelo o año" value={form.model} onChange={e => setForm({ ...form, model: e.target.value })} /></label></div><label>Serie, IMEI o placa<input placeholder="Opcional" value={form.serial_number} onChange={e => setForm({ ...form, serial_number: e.target.value })} /></label><label>Problema reportado<textarea required rows={4} placeholder="Describí los síntomas y lo que solicita el cliente…" value={form.issue} onChange={e => setForm({ ...form, issue: e.target.value })} /></label><label>Técnico responsable<input placeholder="Se puede asignar después" value={form.assigned_to} onChange={e => setForm({ ...form, assigned_to: e.target.value })} /></label>{error && <p className="form-error">{error}</p>}</div><div className="modal-actions"><button type="button" className="secondary" onClick={close}>Cancelar</button><button className="primary" disabled={busy || !form.customer_id}>{busy ? 'Creando…' : 'Crear ticket'}</button></div></form></div>;
}

export default function App() {
  const [page, setPage] = useState('dashboard'); const [dashboard, setDashboard] = useState<DashboardData | null>(null); const [tickets, setTickets] = useState<Ticket[]>([]); const [customers, setCustomers] = useState<Customer[]>([]); const [business, setBusiness] = useState<Business>({ name: 'Next-Fix', phone: '', address: '', currency: 'CRC', accent: '#c8ff45', accent_secondary: '#7c5cff', ticket_prefix: 'NF' }); const [selected, setSelected] = useState<Ticket | null>(null); const [newOpen, setNewOpen] = useState(false); const [search, setSearch] = useState(''); const [status, setStatus] = useState(''); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const refresh = async () => { try { const [d, t, c, b] = await Promise.all([api.dashboard(), api.tickets(search, status), api.customers(), api.business()]); setDashboard(d); setTickets(t); setCustomers(c); setBusiness(b); setError(''); } catch (e) { setError((e as Error).message); } finally { setLoading(false); } };
  useEffect(() => { void refresh(); }, []);
  useEffect(() => { if (!loading) { const timer = setTimeout(() => void api.tickets(search, status).then(setTickets), 180); return () => clearTimeout(timer); } }, [search, status]);
  const content = useMemo(() => { if (page === 'tickets') return <TicketsPage tickets={tickets} currency={business.currency} onSelect={setSelected} search={search} setSearch={setSearch} status={status} setStatus={setStatus} />; if (page === 'customers') return <CustomersPage customers={customers} />; if (page === 'inventory') return <InventoryPage />; if (page === 'settings') return <SettingsPage business={business} saved={async b => setBusiness(await api.updateBusiness(b))} />; return <Dashboard data={dashboard} currency={business.currency} goTickets={() => setPage('tickets')} onNew={() => setNewOpen(true)} />; }, [page, tickets, customers, business, dashboard, search, status]);
  if (loading) return <div className="splash"><span><Wrench /></span><strong>Next-Fix</strong><p>Preparando tu espacio de trabajo…</p></div>;
  return <Shell page={page} setPage={setPage} business={business} onNew={() => setNewOpen(true)}>{error && <div className="error-banner">{error} <button onClick={() => void refresh()}>Reintentar</button></div>}{content}{selected && <TicketDrawer ticket={selected} currency={business.currency} close={() => setSelected(null)} update={ticket => { setSelected(ticket); setTickets(items => items.map(x => x.id === ticket.id ? ticket : x)); void api.dashboard().then(setDashboard); }} />}{newOpen && <NewTicket customers={customers} close={() => setNewOpen(false)} created={ticket => { setNewOpen(false); setSelected(ticket); void refresh(); }} />}</Shell>;
}

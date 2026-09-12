import { useState } from 'react';
import { Database, Save } from 'lucide-react';
import { Loading, Notice } from '../components/Common';
import { post, put } from '../lib/api';
import { useAction, useResource } from '../lib/hooks';
import type { Business } from '../types';

function BusinessForm({ initial }: { initial: Business }) {
  const [form, setForm] = useState(initial);
  const action = useAction();
  function field(key: keyof Business, value: string) { setForm(current => ({ ...current, [key]: value })); }
  return <section className="panel"><h2>Identidad del negocio</h2><form onSubmit={e => { e.preventDefault(); void action.run(() => put('/admin/business', form), 'Configuración guardada.'); }}>
    <label>Nombre del local<input required maxLength={100} value={form.name} onChange={e => field('name', e.target.value)} /></label>
    <label>Frase del menú<input maxLength={160} value={form.tagline} onChange={e => field('tagline', e.target.value)} /></label>
    <div className="form-row"><label>SINPE Móvil (8 dígitos)<input inputMode="numeric" pattern="[0-9]{8}" maxLength={8} value={form.sinpe_phone} onChange={e => field('sinpe_phone', e.target.value)} /></label><label>Teléfono<input maxLength={20} value={form.phone} onChange={e => field('phone', e.target.value)} /></label></div>
    <label>Dirección<textarea maxLength={200} value={form.address} onChange={e => field('address', e.target.value)} /></label>
    <Notice error={action.error} message={action.message} /><button className="primary" disabled={action.busy}><Save size={17} /> Guardar cambios</button>
  </form></section>;
}
export default function Settings() {
  const business = useResource<Business>('/business', 60000);
  const action = useAction();
  return <><div className="page-heading"><div><p className="eyebrow">A TU MANERA</p><h1>Mi negocio</h1><p>La información de tu local y el cuidado de tus datos.</p></div></div><Notice error={business.error} />
    <div className="two-columns">{business.data ? <BusinessForm initial={business.data} /> : <Loading />}
      <section className="panel"><div className="section-title"><Database /><h2>Respaldos</h2></div><p>El servidor guarda una copia automática diaria mientras está encendido. También podés crear una antes de hacer cambios importantes.</p>
        <button className="secondary" disabled={action.busy} onClick={() => void action.run(async () => {
          const result = await post<{ message: string; filename: string }>('/admin/backup', {});
          return result;
        }, 'Respaldo creado en la carpeta data/backups del servidor.')}><Database size={17} /> Crear respaldo ahora</button>
        <Notice error={action.error} message={action.message} />
        <p className="small muted">Copiá periódicamente los respaldos a otra unidad para protegerte ante un fallo de la computadora.</p>
        <hr /><h2>Versión inicial · 0.1</h2><p className="small muted">Los pagos con tarjeta y SINPE se verifican manualmente. Esta versión registra pedidos y ventas; todavía no emite comprobantes electrónicos ni gestiona devoluciones.</p>
      </section></div></>;
}


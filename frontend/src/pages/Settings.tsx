import { useState } from 'react';
import { Database, Save, Palette, Store, Download } from 'lucide-react';
import { Loading, Notice } from '../components/Common';
import ImagePicker from '../components/ImagePicker';
import { downloadFile, post, put } from '../lib/api';
import { useAction, useResource } from '../lib/hooks';
import { contrast, defaults, themeVariables } from '../lib/theme';
import { dateTime } from '../lib/format';
import type { Backup, Business, FiscalProfile } from '../types';

const palettes = [
  { name: 'Bosque', colors: ['#184c3b', '#e99a53', '#f6f7f3', '#ffffff', '#233b32'] },
  { name: 'Terracota', colors: ['#a43e29', '#e6aa43', '#fff7ed', '#ffffff', '#40271e'] },
  { name: 'Océano', colors: ['#174ea6', '#12b8b0', '#f0f6fc', '#ffffff', '#172d43'] },
  { name: 'Noche', colors: ['#c3a4ff', '#f5bc65', '#15151d', '#242432', '#f4f0fa'] },
  { name: 'Café crema', colors: ['#674536', '#ce965c', '#f7f0e8', '#fffaf4', '#35271f'] },
  { name: 'Tropical', colors: ['#006b59', '#ffbc42', '#effaf4', '#ffffff', '#163e33'] },
  { name: 'Cereza', colors: ['#ac234a', '#f5b764', '#fff2f5', '#ffffff', '#442130'] },
  { name: 'Lavanda', colors: ['#6940a5', '#dfa965', '#f6f2fc', '#ffffff', '#332342'] },
  { name: 'Carbón y oro', colors: ['#e6bb62', '#e38965', '#191b1b', '#272b2a', '#f5f0e4'] },
  { name: 'Arena', colors: ['#77573b', '#b46c38', '#faf4e8', '#fffdf8', '#392e23'] },
  { name: 'Menta', colors: ['#237767', '#e6a58c', '#f0faf6', '#ffffff', '#203e36'] },
  { name: 'Azul marino', colors: ['#183b61', '#dc9b46', '#f2f5f9', '#ffffff', '#1f3046'] },
];
const colorFields = [
  ['primary_color', 'Color principal'], ['accent_color', 'Color de acento'],
  ['background_color', 'Color de fondo'], ['surface_color', 'Color de tarjetas'],
  ['text_color', 'Color de texto'],
] as const;

function BusinessForm({ initial }: { initial: Business }) {
  const [form, setForm] = useState(initial);
  const [uploads, setUploads] = useState<Record<string, boolean>>({});
  const action = useAction();
  const uploading = Object.values(uploads).some(Boolean);
  function field<K extends keyof Business>(key: K, value: Business[K]) {
    setForm(current => ({ ...current, [key]: value }));
  }
  const validColors = colorFields.every(([key]) => /^#[a-f\d]{6}$/i.test(form[key]));
  const lowContrast = validColors && (contrast(form.text_color, form.surface_color) < 4.5
    || contrast(form.text_color, form.background_color) < 4.5);
  return <form className="settings-form" onSubmit={e => {
    e.preventDefault();
    void action.run(() => put('/admin/business', form), 'Configuración guardada.');
  }}>
    <section className="panel"><div className="section-title"><Store /><h2>Identidad del negocio</h2></div>
      <div className="form-row"><label>Nombre del local<input required maxLength={100} value={form.name} onChange={e => field('name', e.target.value)} /></label>
        <label>Frase del menú<input maxLength={160} value={form.tagline} onChange={e => field('tagline', e.target.value)} /></label></div>
      <div className="form-row"><label>SINPE Móvil (8 dígitos)<input inputMode="numeric" pattern="[0-9]{8}" maxLength={8} value={form.sinpe_phone} onChange={e => field('sinpe_phone', e.target.value)} /></label>
        <label>Teléfono<input maxLength={20} value={form.phone} onChange={e => field('phone', e.target.value)} /></label></div>
      <label>Dirección<textarea maxLength={200} value={form.address} onChange={e => field('address', e.target.value)} /></label>
      <div className="form-row"><ImagePicker label="Logo del negocio" value={form.logo_url} onChange={v => field('logo_url', v)} onBusy={v => setUploads(s => ({ ...s, logo: v }))} />
        <ImagePicker label="Portada del menú" value={form.cover_url} onChange={v => field('cover_url', v)} onBusy={v => setUploads(s => ({ ...s, cover: v }))} /></div>
    </section>
    <section className="panel"><div className="section-title"><Palette /><h2>Tu paleta de colores</h2></div>
      <p className="small muted">Elegí cada color libremente. Las sugerencias son un punto de partida y se pueden modificar.</p>
      <div className="palette-presets">{palettes.map(p => <button type="button" className="secondary" key={p.name} aria-pressed={colorFields.every(([key], i) => form[key].toLowerCase() === p.colors[i])} onClick={() => {
        setForm(s => ({ ...s, ...Object.fromEntries(colorFields.map(([key], i) => [key, p.colors[i]])) }));
      }}><span className="swatches">{p.colors.slice(0, 3).map(c => <i key={c} style={{ background: c }} />)}</span>{p.name}</button>)}</div>
      <div className="color-grid">{colorFields.map(([key, label]) => <label key={key}>{label}<span className="color-control">
        <input type="color" aria-label={'Selector de ' + label.toLowerCase()} value={/^#[a-f\d]{6}$/i.test(form[key]) ? form[key] : defaults[key]} onChange={e => field(key, e.target.value)} />
        <input aria-label={label + ' HEX'} pattern="#[a-fA-F0-9]{6}" required maxLength={7} value={form[key]} onChange={e => field(key, e.target.value)} />
      </span></label>)}</div>
      {lowContrast && <p className="notice">El texto tiene poco contraste con el fondo o las tarjetas. Elegí un texto más claro u oscuro para facilitar la lectura.</p>}
      <div className="theme-preview" style={themeVariables(form)}>
        <p className="eyebrow">VISTA PREVIA</p><div className="preview-brand">{form.logo_url && <img src={form.logo_url} alt="" />}<strong>{form.name}</strong></div>
        <p>{form.tagline}</p><div className="preview-card"><strong>Tu producto favorito</strong><p>Así se verá tu menú con esta paleta.</p><span className="preview-price">₡3 500</span><span className="primary">Agregar al pedido</span></div>
      </div>
      <button className="text-button" type="button" onClick={() => setForm(s => ({ ...s, ...Object.fromEntries(colorFields.map(([key]) => [key, defaults[key]])) }))}>Restaurar colores originales</button>
    </section>
    <section className="panel"><h2>Menú y atención</h2>
      <label>Título de portada<input required maxLength={100} value={form.hero_title} onChange={e => field('hero_title', e.target.value)} /></label>
      <label>Horario de atención<textarea placeholder="Lunes a sábado, 7:00 a. m. a 8:00 p. m." maxLength={300} value={form.opening_hours} onChange={e => field('opening_hours', e.target.value)} /></label>
      <p className="small muted">El horario se muestra en el menú. Controlá la recepción de pedidos con el interruptor.</p>
      <label className="check-label"><input type="checkbox" checked={form.accepting_orders} onChange={e => field('accepting_orders', e.target.checked)} /> Recibir nuevos pedidos</label>
      <label>Mensaje al pausar pedidos<input required maxLength={100} value={form.closed_message} onChange={e => field('closed_message', e.target.value)} /></label>
      <label>Mensaje en el recibo<input maxLength={200} value={form.receipt_footer} onChange={e => field('receipt_footer', e.target.value)} /></label>
    </section>
    <div className="settings-save"><Notice error={action.error} message={action.message} /><button className="primary" disabled={action.busy || uploading || !validColors}><Save size={17} />{uploading ? 'Esperá a que terminen las imágenes…' : 'Guardar cambios'}</button><span className="small muted">La vista previa se publica al guardar.</span></div>
  </form>;
}

function FiscalForm({ initial }: { initial: FiscalProfile }) {
  const [form, setForm] = useState(initial);
  const action = useAction();
  return <form onSubmit={e => { e.preventDefault(); void action.run(() => put('/admin/fiscal', form), 'Datos fiscales guardados localmente.'); }}>
    <p className="notice">Preparación para facturación electrónica de Costa Rica. Aún no se generan ni envían comprobantes a Hacienda.</p>
    {([['legal_name', 'Razón social'], ['identification', 'Identificación fiscal'], ['activity_code', 'Código de actividad económica'], ['email', 'Correo fiscal'], ['branch_code', 'Código de sucursal'], ['terminal_code', 'Código de terminal']] as const).map(([key, label]) =>
      <label key={key}>{label}<input value={form[key]} type={key === 'email' ? 'email' : 'text'}
        maxLength={{ legal_name: 160, identification: 20, activity_code: 10, email: 160, branch_code: 3, terminal_code: 5 }[key]}
        onChange={e => setForm(s => ({ ...s, [key]: e.target.value }))} /></label>)}
    <Notice error={action.error} message={action.message} /><button className="secondary" disabled={action.busy}>Guardar datos fiscales</button>
  </form>;
}

export default function Settings() {
  const business = useResource<Business>('/business');
  const fiscal = useResource<FiscalProfile>('/admin/fiscal');
  const backups = useResource<Backup[]>('/admin/backups', 60000);
  const action = useAction();
  return <><div className="page-heading"><div><p className="eyebrow">A TU MANERA</p><h1>Mi negocio</h1><p>Tu marca, tu menú y tus datos, en tu propio servidor.</p></div><span className="badge status-ready">Operación local</span></div>
    <Notice error={business.error || fiscal.error || backups.error} />
    <div className="settings-layout"><div>{business.data ? <BusinessForm initial={business.data} /> : <Loading />}</div><aside className="settings-side">
      <section className="panel"><div className="section-title"><Database /><h2>Respaldos completos</h2></div><p className="small">Incluyen ventas, usuarios, configuración, logos y fotografías. Se crea uno diario mientras el servidor está encendido.</p>
        <button className="secondary" disabled={action.busy} onClick={() => void action.run(() => post('/admin/backup', {}), 'Respaldo completo creado. Ya podés descargarlo.')}><Database size={17} /> Crear respaldo ahora</button>
        <Notice error={action.error} message={action.message} />
        <div className="backup-list">{backups.data?.slice(0, 5).map(b => <div key={b.filename}><span>{dateTime(b.created_at)}<small>{(b.size / 1024).toFixed(0)} KB · {b.filename.endsWith('.zip') ? 'Datos e imágenes' : 'Solo base de datos'}</small></span><button className="icon-button" aria-label={'Descargar ' + b.filename} disabled={action.busy} onClick={() => void action.run(() => downloadFile('/admin/backups/' + b.filename, b.filename))}><Download size={17} /></button></div>)}</div>
        <p className="small muted">Guardá una copia en otra unidad. Para restaurar, detené el servidor y seguí RESTORE.txt del ZIP.</p>
      </section>
      <section className="panel"><h2>Acceso desde otros equipos</h2><p className="small">En la misma red, abrí la dirección IP de esta computadora con el puerto 8000. El servidor debe permanecer encendido.</p>
        <label>Dirección actual del menú<input readOnly value={location.origin + '/#/'} onFocus={e => e.target.select()} /></label>
        {['localhost', '127.0.0.1'].includes(location.hostname) && <p className="small muted">Esta dirección solo sirve en esta computadora. En otros dispositivos, reemplazá localhost por la IP del servidor.</p>}
      </section>
      <section className="panel"><details><summary><strong>Datos fiscales · Costa Rica</strong></summary>{fiscal.data && <FiscalForm initial={fiscal.data} />}</details></section>
      <section className="panel"><h2>Pagos y facturación</h2><p className="small">Tarjeta y SINPE se verifican en caja. El cobro automático con tarjeta y el envío de comprobantes a Hacienda requieren una integración externa y conexión a internet.</p><p className="small muted">Los recibos imprimibles son comprobantes de pedido, sin validez como factura electrónica.</p></section>
    </aside></div></>;
}

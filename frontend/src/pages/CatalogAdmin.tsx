import { useState } from 'react';
import { Pencil, Plus, X } from 'lucide-react';
import { Empty, Notice } from '../components/Common';
import { post, put } from '../lib/api';
import { money, parseMoney } from '../lib/format';
import { useAction, useResource } from '../lib/hooks';
import type { Catalog, Product } from '../types';
import ImagePicker from '../components/ImagePicker';

function ProductEditor({ product, catalog, close }: { product?: Product; catalog: Catalog; close: () => void }) {
  const [name, setName] = useState(product?.name ?? '');
  const [description, setDescription] = useState(product?.description ?? '');
  const [category, setCategory] = useState(product?.category_id ?? catalog.categories[0]?.id ?? 0);
  const [price, setPrice] = useState(product ? String(product.price_cents / 100) : '');
  const [icon, setIcon] = useState(product?.icon ?? '🍽️');
  const [available, setAvailable] = useState(product?.available ?? true);
  const [image, setImage] = useState(product?.image_url ?? '');
  const [uploading, setUploading] = useState(false);
  const [featured, setFeatured] = useState(product?.featured ?? false);
  const [sortOrder, setSortOrder] = useState(product?.sort_order ?? 0);
  const [allergens, setAllergens] = useState(product?.allergens ?? '');
  const [cabys, setCabys] = useState(product?.cabys ?? '');
  const action = useAction();
  return <section className="panel"><div className="row-between"><h2>{product ? 'Editar producto' : 'Nuevo producto'}</h2><button className="icon-button" aria-label="Cerrar editor" onClick={close}><X size={20} /></button></div>
    <form onSubmit={e => { e.preventDefault(); void action.run(async () => {
      const body = { name, description, category_id: category, price_cents: parseMoney(price), available, icon,
        image_url: image, featured, sort_order: sortOrder, allergens, cabys };
      if (product) await put('/admin/products/' + product.id, body);
      else await post('/admin/products', body);
      close();
    }); }}>
      <label>Nombre<input value={name} required maxLength={100} onChange={e => setName(e.target.value)} /></label>
      <label>Descripción<textarea value={description} maxLength={300} onChange={e => setDescription(e.target.value)} /></label>
      <ImagePicker label="Foto del producto" value={image} onChange={setImage} onBusy={setUploading} />
      <div className="form-row"><label>Categoría<select value={category} required onChange={e => setCategory(Number(e.target.value))}>{catalog.categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label><label>Precio final (₡)<input type="number" min="0.01" step="0.01" value={price} required onChange={e => setPrice(e.target.value)} /></label></div>
      <label>Ícono del producto<select value={icon} onChange={e => setIcon(e.target.value)}>{['🍽️', '🍛', '🍔', '🍟', '🍳', '🫓', '🥤', '☕', '🍕', '🌮', '🥪', '🍰', '🥗', '🍗'].map(i => <option key={i} value={i}>{i}</option>)}</select></label>
      <label className="check-label"><input type="checkbox" checked={available} onChange={e => setAvailable(e.target.checked)} /> Disponible para pedir</label>
      <label className="check-label"><input type="checkbox" checked={featured} onChange={e => setFeatured(e.target.checked)} /> Destacar en el menú</label>
      <label>Orden del producto<input type="number" min="0" max="9999" required value={sortOrder} onChange={e => setSortOrder(Number(e.target.value))} /></label>
      <label>Alérgenos e información alimentaria<textarea maxLength={300} placeholder="Ej.: contiene leche, huevo y gluten." value={allergens} onChange={e => setAllergens(e.target.value)} /></label>
      <label>Código CABYS (opcional)<input inputMode="numeric" maxLength={13} pattern="[0-9]{13}" value={cabys} onChange={e => setCabys(e.target.value)} /></label>
      <p className="small muted">Los destacados aparecen primero. Un orden menor aparece antes. CABYS se guarda como preparación fiscal; aún no se emiten facturas.</p>
      <Notice error={action.error} /><button className="primary" disabled={action.busy || uploading || !category}>Guardar producto</button>
    </form></section>;
}

export default function CatalogAdmin() {
  const catalog = useResource<Catalog>('/admin/catalog');
  const [editing, setEditing] = useState<Product | 'new' | null>(null);
  const [categoryName, setCategoryName] = useState('');
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [categoryOrder, setCategoryOrder] = useState(0);
  const action = useAction();
  return <><div className="page-heading"><div><p className="eyebrow">DALE VIDA AL MENÚ</p><h1>Productos y categorías</h1><p>Los cambios aparecen en el autoservicio. Los pedidos existentes conservan su precio.</p></div><button className="primary" onClick={() => setEditing('new')} disabled={!catalog.data?.categories.length}><Plus size={18} /> Nuevo producto</button></div>
    <Notice error={catalog.error || action.error} message={action.message} />
    <div className="catalog-admin-layout"><section className="panel">{!catalog.data?.products.length ? <Empty>Creá una categoría y agregá tu primer producto.</Empty> : <div className="table-scroll"><table><thead><tr><th>Producto</th><th>Precio</th><th>Estado</th><th><span className="visually-hidden">Acciones</span></th></tr></thead><tbody>{catalog.data.products.map(p => <tr key={p.id}><td><div className="product-cell">{p.image_url ? <img className="product-thumb" src={p.image_url} alt={p.name} /> : <span>{p.icon}</span>}<div><strong>{p.featured ? '★ ' : ''}{p.name}</strong><small>{catalog.data?.categories.find(c => c.id === p.category_id)?.name}</small></div></div></td><td>{money(p.price_cents)}</td><td><button className={'badge toggle-badge ' + (p.available ? 'status-ready' : 'status-cancelled')} disabled={action.busy} onClick={() => void action.run(() => {
      const { id, ...body } = p;
      return put('/admin/products/' + id, { ...body, available: !p.available });
    })}>{p.available ? 'Disponible' : 'Agotado'}</button></td><td><button className="icon-button" aria-label={'Editar ' + p.name} onClick={() => setEditing(p)}><Pencil size={17} /></button></td></tr>)}</tbody></table></div>}</section>
    <div>{editing && catalog.data ? <ProductEditor key={editing === 'new' ? 'new' : editing.id} product={editing === 'new' ? undefined : editing} catalog={catalog.data} close={() => setEditing(null)} /> : <section className="panel"><h2>Categorías</h2><div className="category-list">{catalog.data?.categories.map(c => <button key={c.id} className="row-between" onClick={() => { setCategoryId(c.id); setCategoryName(c.name); setCategoryOrder(c.sort_order); }}>{c.name}<Pencil size={14} /></button>)}</div><label>Orden de la categoría<input type="number" min="0" max="9999" value={categoryOrder} onChange={e => setCategoryOrder(Number(e.target.value))} /></label><form onSubmit={e => { e.preventDefault(); void action.run(async () => {
      if (categoryId) await put('/admin/categories/' + categoryId, { name: categoryName, sort_order: categoryOrder });
      else await post('/admin/categories', { name: categoryName, sort_order: categoryOrder });
      setCategoryName(''); setCategoryId(null); setCategoryOrder(0);
    }, 'Categoría guardada.'); }}><label>{categoryId ? 'Editar categoría' : 'Nueva categoría'}<input required maxLength={60} value={categoryName} onChange={e => setCategoryName(e.target.value)} /></label><button className="secondary" disabled={action.busy}>Guardar categoría</button>{categoryId && <button type="button" className="text-button" onClick={() => { setCategoryId(null); setCategoryName(''); }}>Cancelar edición</button>}</form></section>}</div></div>
  </>;
}

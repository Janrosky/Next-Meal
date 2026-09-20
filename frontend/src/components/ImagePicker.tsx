import { useId, useState } from 'react';
import { api } from '../lib/api';
import { Notice } from './Common';

export default function ImagePicker({ label, value, onChange, onBusy }: {
  label: string; value: string; onChange: (url: string) => void; onBusy: (busy: boolean) => void;
}) {
  const id = useId();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function upload(file?: File) {
    if (!file || busy) return;
    if (file.size > 5 * 1024 * 1024) { setError('La imagen supera los 5 MB.'); return; }
    setBusy(true); onBusy(true); setError('');
    try {
      const result = await api<{ url: string }>('/admin/media', {
        method: 'POST', body: file, headers: { 'Content-Type': 'application/octet-stream' },
      });
      onChange(result.url);
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); onBusy(false); }
  }
  return <div className="image-picker">
    <label htmlFor={id}>{label}</label>
    {value && <img src={value} alt={'Vista previa: ' + label} />}
    <input id={id} type="file" accept="image/jpeg,image/png,image/webp" disabled={busy}
      onChange={e => { void upload(e.target.files?.[0]); e.target.value = ''; }} />
    <p className="small muted">{busy ? 'Procesando imagen…' : 'JPG, PNG o WebP. Máximo 5 MB. Guardada en este servidor.'}</p>
    {value && <button className="text-button" type="button" disabled={busy} onClick={() => onChange('')}>Quitar imagen</button>}
    <Notice error={error} />
  </div>;
}

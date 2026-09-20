import { useState } from 'react';
import { Notice } from '../components/Common';
import { post, put } from '../lib/api';
import { roleLabel } from '../lib/format';
import { useAction, useResource } from '../lib/hooks';
import type { Role, User } from '../types';

export default function Employees({ currentUser }: { currentUser: User }) {
  const users = useResource<User[]>('/admin/users');
  const action = useAction();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Role>('cashier');
  const [editing, setEditing] = useState<User | null>(null);
  const [active, setActive] = useState(true);
  function reset() { setEditing(null); setUsername(''); setPassword(''); setRole('cashier'); setActive(true); }
  return <><div className="page-heading"><div><p className="eyebrow">UN EQUIPO BIEN COORDINADO</p><h1>Empleados</h1><p>Cada persona tiene su cuenta y los permisos que necesita.</p></div></div><Notice error={users.error || action.error} message={action.message} />
    <div className="two-columns"><section className="panel"><h2>Tu equipo</h2>{users.data?.map(user => <div className="employee-row" key={user.id}><span className="avatar">{user.username.slice(0, 2).toUpperCase()}</span><div><strong>{user.username}{user.id === currentUser.id ? ' (vos)' : ''}</strong><small>{roleLabel[user.role]} · {user.active ? 'Activo' : 'Desactivado'}</small></div><button className="secondary" onClick={() => { setEditing(user); setUsername(user.username); setRole(user.role); setActive(!!user.active); setPassword(''); }}>Editar</button></div>)}</section>
    <section className="panel"><h2>{editing ? 'Editar cuenta' : 'Agregar empleado'}</h2><form onSubmit={e => { e.preventDefault(); void action.run(async () => {
      if (editing) await put('/admin/users/' + editing.id, { role, active, password: password || null });
      else await post('/admin/users', { username, password, role });
      reset();
    }, 'Cuenta guardada.'); }}>
      <label>Usuario<input value={username} disabled={!!editing} required minLength={3} maxLength={40} pattern="[a-z0-9_.-]{3,40}" onChange={e => setUsername(e.target.value.toLowerCase())} autoComplete="off" /></label>
      <label>{editing ? 'Nueva contraseña (opcional)' : 'Contraseña'}<input type="password" required={!editing} value={password} onChange={e => setPassword(e.target.value)} autoComplete="new-password" /></label>
      <label>Perfil<select value={role} onChange={e => setRole(e.target.value as Role)}>{(['cashier', 'kitchen', 'admin'] as Role[]).map(r => <option key={r} value={r}>{roleLabel[r]}</option>)}</select></label>
      {editing && <label className="check-label"><input type="checkbox" checked={active} onChange={e => setActive(e.target.checked)} /> Cuenta activa</label>}
      <button className="primary" disabled={action.busy}>Guardar cuenta</button>{editing && <button type="button" className="text-button" onClick={reset}>Cancelar edición</button>}
      <p className="small muted">Los cambios de perfil, contraseña o estado cierran las sesiones de esa cuenta.</p>
    </form></section></div></>;
}

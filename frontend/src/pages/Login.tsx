import { useState } from 'react';
import { ArrowLeft, ArrowRight, LockKeyhole } from 'lucide-react';
import { Brand, Notice } from '../components/Common';
import { post, setSessionToken } from '../lib/api';
import { useAction } from '../lib/hooks';
import type { User } from '../types';

export default function Login({ onLogin }: { onLogin: (user: User) => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const action = useAction();
  return <div className="login-page"><div className="login-story"><Brand /><div><p className="eyebrow">TODO EN SU PUNTO.</p><h1>Menos enredos.<br /><em>Más sabor.</em></h1><p>Tu equipo, tus pedidos y tu negocio,<br />trabajando en la misma dirección.</p></div><small>Hecho para el ritmo de tu restaurante.</small></div>
    <main className="login-form"><a className="back-link" href="#/"><ArrowLeft size={16} /> Volver al menú</a>
      <div className="login-icon"><LockKeyhole /></div><h1>¡Qué bueno verte!</h1><p className="muted">Ingresá con tu cuenta de empleado.</p>
      <form onSubmit={e => { e.preventDefault(); void action.run(async () => {
        const result = await post<{ token: string; user: User }>('/auth/login', { username, password });
        setSessionToken(result.token); onLogin(result.user);
      }); }}>
        <label>Usuario<input autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} required maxLength={40} autoFocus /></label>
        <label>Contraseña<input type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} required maxLength={128} /></label>
        <Notice error={action.error} /><button className="primary wide" disabled={action.busy}>{action.busy ? 'Ingresando…' : 'Ingresar'}<ArrowRight size={18} /></button>
      </form><p className="muted small">Tu administrador crea y administra las cuentas del equipo.</p>
    </main></div>;
}


import { useEffect, useState } from 'react';
import { Banknote, ChefHat, ClipboardList, ExternalLink, LayoutDashboard, LogOut, Package, Settings as SettingsIcon, Users, Wallet } from 'lucide-react';
import { Brand, Loading, Notice } from './components/Common';
import { api, post, sessionToken, setSessionToken } from './lib/api';
import { roleLabel } from './lib/format';
import { useLiveUpdates, useResource } from './lib/hooks';
import type { Business, User } from './types';
import Kiosk from './pages/Kiosk';
import Login from './pages/Login';
import Cashier from './pages/Cashier';
import Kitchen from './pages/Kitchen';
import Shifts from './pages/Shifts';
import Dashboard from './pages/Dashboard';
import CatalogAdmin from './pages/CatalogAdmin';
import Employees from './pages/Employees';
import Settings from './pages/Settings';
import { BusinessProvider } from './lib/theme';
import History from './pages/History';

function Workspace({ user, logout }: { user: User; logout: () => Promise<void> }) {
  const [page, setPage] = useState(user.role === 'admin' ? 'dashboard' : user.role === 'kitchen' ? 'kitchen' : 'cashier');
  const connected = useLiveUpdates();
  const business = useResource<Business>('/business', 60000);
  const [logoutError, setLogoutError] = useState('');
  const navigation = [
    { id: 'dashboard', label: 'Resumen', icon: LayoutDashboard, roles: ['admin'] },
    { id: 'cashier', label: 'Caja', icon: Banknote, roles: ['admin', 'cashier'] },
    { id: 'kitchen', label: 'Cocina', icon: ChefHat, roles: ['admin', 'kitchen'] },
    { id: 'shifts', label: 'Turno de caja', icon: Wallet, roles: ['admin', 'cashier'] },
    { id: 'catalog', label: 'Productos', icon: Package, roles: ['admin'] },
    { id: 'employees', label: 'Empleados', icon: Users, roles: ['admin'] },
    { id: 'history', label: 'Historial', icon: ClipboardList, roles: ['admin'] },
    { id: 'settings', label: 'Mi negocio', icon: SettingsIcon, roles: ['admin'] },
  ].filter(item => item.roles.includes(user.role));
  return <div className="workspace"><aside className="sidebar"><Brand /><p className="sidebar-label">TU ESPACIO DE TRABAJO</p><nav>{navigation.map(item => <button key={item.id} className={page === item.id ? 'active' : ''} onClick={() => setPage(item.id)}><item.icon size={20} />{item.label}</button>)}</nav>
    <a className="menu-link" href="#/" target="_blank" rel="noreferrer"><ExternalLink size={18} /> Abrir autoservicio</a>
    <div className="sidebar-bottom"><div className="employee-identity"><span className="avatar">{user.username.slice(0, 2).toUpperCase()}</span><div><strong>{user.username}</strong><small>{roleLabel[user.role]}</small></div></div>
      <button className="logout" onClick={() => { void logout().catch(error => setLogoutError((error as Error).message)); }}><LogOut size={17} /> Cerrar sesión</button><Notice error={logoutError} /></div>
  </aside><div className="workspace-content"><header className="workspace-header"><span>{business.data?.name ?? 'Mi Soda'} <span className="muted">/ Operación</span></span><span className={'connection ' + (connected ? 'connected' : '')}><i />{connected ? 'En vivo' : 'Actualización periódica'}</span></header><main className="staff-main">
    {page === 'dashboard' && <Dashboard />}{page === 'cashier' && <Cashier />}{page === 'kitchen' && <Kitchen />}
    {page === 'shifts' && <Shifts />}{page === 'catalog' && <CatalogAdmin />}{page === 'employees' && <Employees currentUser={user} />}
    {page === 'settings' && <Settings />}{page === 'history' && <History />}
  </main></div></div>;
}

function Staff() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(!!sessionToken());
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    if (sessionToken()) api<User>('/auth/me').then(user => { if (active) setUser(user); })
      .catch(error => { if (active) setError((error as Error).message); })
      .finally(() => { if (active) setLoading(false); });
    const expired = () => { setUser(null); setLoading(false); };
    window.addEventListener('session-expired', expired);
    return () => { active = false; window.removeEventListener('session-expired', expired); };
  }, []);
  if (loading) return <Loading />;
  if (!user) return <><Notice error={error} /><Login onLogin={user => { setUser(user); setError(''); }} /></>;
  return <Workspace user={user} logout={async () => {
    await post('/auth/logout', {});
    setSessionToken(null); setUser(null);
  }} />;
}

export default function App() {
  const [staff, setStaff] = useState(location.hash.startsWith('#/staff'));
  useEffect(() => {
    const changed = () => setStaff(location.hash.startsWith('#/staff'));
    window.addEventListener('hashchange', changed);
    return () => window.removeEventListener('hashchange', changed);
  }, []);
  return <BusinessProvider>{staff ? <Staff /> : <Kiosk />}</BusinessProvider>;
}

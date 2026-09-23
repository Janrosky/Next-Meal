import { createContext, useContext, useEffect, type CSSProperties, type ReactNode } from 'react';
import { useResource } from './hooks';
import type { Business } from '../types';

export const defaults: Business = {
  name: 'Mi Soda', tagline: 'Hecho aquí. Servido con cariño.', sinpe_phone: '', phone: '', address: '',
  logo_url: '', cover_url: '', primary_color: '#184c3b', accent_color: '#e99a53',
  background_color: '#f6f7f3', surface_color: '#ffffff', text_color: '#233b32',
  hero_title: 'Tu antojo, recién hecho.', receipt_footer: '¡Gracias por tu visita!',
  opening_hours: '', accepting_orders: true, closed_message: 'En este momento no recibimos pedidos.',
};
const BusinessContext = createContext<Business>(defaults);
export const useBusiness = () => useContext(BusinessContext);

function luminance(hex: string) {
  const c = hex.match(/[a-f\d]{2}/gi)!.map(v => parseInt(v, 16) / 255)
    .map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4);
  return .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
}
export function contrast(a: string, b: string) {
  const [lo, hi] = [luminance(a), luminance(b)].sort((x, y) => x - y);
  return (hi + .05) / (lo + .05);
}
export function themeVariables(b: Business): CSSProperties {
  const safe = (color: string, fallback: string) => /^#[a-f\d]{6}$/i.test(color) ? color : fallback;
  const primary = safe(b.primary_color, defaults.primary_color);
  const text = safe(b.text_color, defaults.text_color);
  const surface = safe(b.surface_color, defaults.surface_color);
  const background = safe(b.background_color, defaults.background_color);
  const foreground = (color: string) => contrast('#ffffff', color) >= contrast('#000000', color) ? '#ffffff' : '#000000';
  return {
    '--green': primary, '--green-dark': 'color-mix(in srgb, var(--green), black 15%)',
    '--orange': safe(b.accent_color, defaults.accent_color),
    '--on-primary': foreground(primary), '--on-accent': foreground(safe(b.accent_color, defaults.accent_color)),
    '--page-bg': background, '--surface': surface, '--text': text,
    '--muted': 'color-mix(in srgb, var(--text) 75%, var(--surface))',
    '--border': 'color-mix(in srgb, var(--text) 22%, var(--surface))',
    '--soft': 'color-mix(in srgb, var(--green) 9%, var(--surface))',
    '--cream': 'color-mix(in srgb, var(--orange) 12%, var(--surface))',
    color: text, backgroundColor: background,
  } as CSSProperties;
}

export function BusinessProvider({ children }: { children: ReactNode }) {
  const resource = useResource<Business>('/business', 15000);
  const business = resource.data ?? defaults;
  useEffect(() => {
    document.title = business.name + ' · Pedidos';
    let icon = document.querySelector<HTMLLinkElement>('link[rel="icon"]');
    if (!icon) { icon = document.createElement('link'); icon.rel = 'icon'; document.head.append(icon); }
    if (business.logo_url) {
      icon.href = business.logo_url;
      icon.removeAttribute('type');
    } else {
      icon.href = '/favicon.svg';
      icon.type = 'image/svg+xml';
    }
    let themeColor = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
    if (!themeColor) {
      themeColor = document.createElement('meta');
      themeColor.name = 'theme-color';
      document.head.append(themeColor);
    }
    themeColor.content = business.primary_color;
    document.documentElement.style.backgroundColor = business.background_color;
  }, [business]);
  return <BusinessContext.Provider value={business}><div className="themed-app" style={themeVariables(business)}>{children}</div></BusinessContext.Provider>;
}

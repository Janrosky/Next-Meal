const TOKEN_KEY = 'sodalocal.session';

export const sessionToken = () => sessionStorage.getItem(TOKEN_KEY);
export function setSessionToken(token: string | null) {
  if (token) sessionStorage.setItem(TOKEN_KEY, token);
  else sessionStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = sessionToken();
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch('/api' + path, {
      ...options,
      signal: controller.signal,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
        ...options.headers,
      },
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      if (response.status === 401 && path !== '/auth/login') {
        setSessionToken(null);
        window.dispatchEvent(new Event('session-expired'));
      }
      const detail = typeof body.detail === 'string'
        ? body.detail
        : 'Revisá los datos ingresados; hay un campo inválido.';
      throw new ApiError(detail, response.status);
    }
    if (response.status === 204) return undefined as T;
    return await response.json() as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('No pudimos comunicarnos con el servidor. Revisá la conexión y volvé a intentar.', 0);
  } finally {
    window.clearTimeout(timeout);
  }
}

export function post<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: 'POST', body: JSON.stringify(body) });
}

export function put<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: 'PUT', body: JSON.stringify(body) });
}

export function refreshResources() {
  window.dispatchEvent(new Event('data-changed'));
}

export function newKey(): string {
  // getRandomValues also works on local HTTP kiosks, unlike randomUUID.
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const hex = Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
  return [hex.slice(0, 8), hex.slice(8, 12), hex.slice(12, 16), hex.slice(16, 20), hex.slice(20)].join('-');
}

export async function downloadSales(day: string) {
  const response = await fetch('/api/admin/sales.csv?day=' + day, {
    headers: { Authorization: 'Bearer ' + sessionToken() },
  });
  if (!response.ok) throw new Error('No se pudo exportar. Revisá tu sesión.');
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = 'ventas-' + day + '.csv';
  link.click();
  URL.revokeObjectURL(url);
}


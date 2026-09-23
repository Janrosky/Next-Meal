import type { Business, Customer, DashboardData, Ticket, TicketStatus } from './types';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch('/api' + path, { ...options, headers: { 'Content-Type': 'application/json', ...options?.headers } });
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || 'No se pudo completar la operación.'); }
  return response.status === 204 ? undefined as T : response.json();
}

export const api = {
  dashboard: () => request<DashboardData>('/dashboard'),
  tickets: (search = '', status = '') => request<Ticket[]>(`/tickets?search=${encodeURIComponent(search)}&status=${encodeURIComponent(status)}`),
  createTicket: (body: object) => request<Ticket>('/tickets', { method: 'POST', body: JSON.stringify(body) }),
  updateTicket: (id: number, body: object) => request<Ticket>(`/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  setStatus: (id: number, status: TicketStatus) => request<Ticket>(`/tickets/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  customers: (search = '') => request<Customer[]>(`/customers?search=${encodeURIComponent(search)}`),
  createCustomer: (body: object) => request<Customer>('/customers', { method: 'POST', body: JSON.stringify(body) }),
  business: () => request<Business>('/business'),
  updateBusiness: (body: object) => request<Business>('/business', { method: 'PATCH', body: JSON.stringify(body) }),
};

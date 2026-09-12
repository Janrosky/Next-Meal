import { useCallback, useEffect, useRef, useState } from 'react';
import { api, refreshResources, sessionToken } from './api';

export function useResource<T>(path: string, interval = 15000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const sequence = useRef(0);
  const reload = useCallback(async () => {
    const version = ++sequence.current;
    try {
      const result = await api<T>(path);
      if (version === sequence.current) { setData(result); setError(''); }
    } catch (error) {
      if (version === sequence.current) setError((error as Error).message);
    }
  }, [path]);
  useEffect(() => {
    setData(null);
    void reload();
    const timer = window.setInterval(() => void reload(), interval);
    const listener = () => void reload();
    window.addEventListener('data-changed', listener);
    return () => {
      sequence.current++;
      window.clearInterval(timer);
      window.removeEventListener('data-changed', listener);
    };
  }, [reload, interval]);
  return { data, error, reload };
}

export function useAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const locked = useRef(false);
  async function run(action: () => Promise<unknown>, success = ''): Promise<boolean> {
    if (locked.current) return false;
    locked.current = true;
    setBusy(true); setError(''); setMessage('');
    try {
      await action();
      setMessage(success);
      refreshResources();
      return true;
    } catch (error) {
      setError((error as Error).message);
      return false;
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }
  return { busy, error, message, run };
}

export function useLiveUpdates() {
  const [connected, setConnected] = useState(false);
  useEffect(() => {
    let stopped = false;
    let socket: WebSocket | null = null;
    let retry: number | undefined;
    const connect = () => {
      if (stopped || !sessionToken()) return;
      const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
      socket = new WebSocket(protocol + '//' + location.host + '/api/events');
      socket.onopen = () => socket?.send(JSON.stringify({ token: sessionToken() }));
      socket.onmessage = event => {
        setConnected(true);
        const message = JSON.parse(event.data);
        if (message.type === 'changed') refreshResources();
      };
      socket.onclose = () => {
        setConnected(false);
        if (!stopped) retry = window.setTimeout(connect, 4000);
      };
      socket.onerror = () => socket?.close();
    };
    connect();
    return () => { stopped = true; window.clearTimeout(retry); socket?.close(); };
  }, []);
  return connected;
}


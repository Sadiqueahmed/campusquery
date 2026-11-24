/**
 * api.js — Centralized fetch calls with error handling.
 */

const API_BASE = '/api';

async function handleResponse(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = body?.error?.message || body?.detail?.[0]?.msg || `Server error (${res.status})`;
    throw new Error(msg);
  }
  return res;
}

/** POST /api/chat */
export async function sendQuestion(question) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  const data = await (await handleResponse(res)).json();
  return data;
}

/** POST /api/export-csv — returns a Blob */
export async function exportCsv(sql) {
  const res = await fetch(`${API_BASE}/export-csv`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.error?.message || 'CSV export failed');
  }
  return res.blob();
}

/** GET /api/health */
export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return (await handleResponse(res)).json();
}

/** GET /api/history */
export async function fetchHistory() {
  const res = await fetch(`${API_BASE}/history`);
  return (await handleResponse(res)).json();
}

/** DELETE /api/history */
export async function clearHistory() {
  const res = await fetch(`${API_BASE}/history`, {
    method: 'DELETE',
  });
  return (await handleResponse(res)).json();
}

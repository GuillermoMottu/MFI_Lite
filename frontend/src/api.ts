const BASE = '/api'

export const api = {
  runDemo: () => fetch(`${BASE}/demo/run`, { method: 'POST' }).then(r => r.json()),
  resetDemo: () => fetch(`${BASE}/demo/reset`, { method: 'POST' }).then(r => r.json()),
  getDemoStatus: () => fetch(`${BASE}/demo/status`).then(r => r.json()),
  getEvents: (limit = 50) => fetch(`${BASE}/events/?limit=${limit}`).then(r => r.json()),
  getEventChain: (correlationId: string) =>
    fetch(`${BASE}/events/chain?correlation_id=${correlationId}`).then(r => r.json()),
  simulateLowStock: () => fetch(`${BASE}/offline/simulate-low-stock`, { method: 'POST' }).then(r => r.json()),
  simulateCloudDown: () => fetch(`${BASE}/offline/simulate-cloud-down`, { method: 'POST' }).then(r => r.json()),
  simulateCloudUp: () => fetch(`${BASE}/offline/simulate-cloud-up`, { method: 'POST' }).then(r => r.json()),
  replay: () => fetch(`${BASE}/offline/replay`, { method: 'POST' }).then(r => r.json()),
  generatePO: () => fetch(`${BASE}/erp/generate-purchase-order`, { method: 'POST' }).then(r => r.json()),
  detectIdle: () => fetch(`${BASE}/production/detect-idle`, { method: 'POST' }).then(r => r.json()),
  bufferStatus: () => fetch(`${BASE}/offline/buffer-status`).then(r => r.json()),
  getStockHistory: () => fetch(`${BASE}/erp/stock-history`).then(r => r.json()),
  getInferenceStatus: () => fetch(`${BASE}/aiml/inference-status`).then(r => r.json()),
  runOfflineNarrative: () =>
    fetch(`${BASE}/demo/run-offline-narrative`, { method: 'POST' }).then(r => r.json()),
}

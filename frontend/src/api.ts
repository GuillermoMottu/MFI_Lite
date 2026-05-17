const BASE = '/api'

let authToken: string | null = typeof window === 'undefined' ? null : localStorage.getItem('mfi_auth_token')

export function setAuthToken(token: string | null) {
  authToken = token
}

function authFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const headers = new Headers(init.headers)
  if (authToken) headers.set('Authorization', `Bearer ${authToken}`)
  return fetch(input, { ...init, headers })
}

export function auditExportUrl(params: {
  format: 'json' | 'csv'
  entity_type?: string
  entity_id?: string
  sku_id?: string
  correlation_id?: string
}) {
  const search = new URLSearchParams()
  search.set('format', params.format)
  if (params.entity_type) search.set('entity_type', params.entity_type)
  if (params.entity_id) search.set('entity_id', params.entity_id)
  if (params.sku_id) search.set('sku_id', params.sku_id)
  if (params.correlation_id) search.set('correlation_id', params.correlation_id)
  return `${BASE}/audit/export?${search.toString()}`
}

export const api = {
  login: (username: string, password: string) =>
    fetch(`${BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo iniciar sesion')
      return json
    }),
  logout: () => authFetch(`${BASE}/auth/logout`, { method: 'POST' }).then(r => r.json()),
  me: () => authFetch(`${BASE}/auth/me`).then(async r => {
    const json = await r.json()
    if (!r.ok) throw new Error(json.detail ?? 'Sesion invalida')
    return json
  }),
  runDemo: () => authFetch(`${BASE}/demo/run`, { method: 'POST' }).then(r => r.json()),
  resetDemo: () => authFetch(`${BASE}/demo/reset`, { method: 'POST' }).then(r => r.json()),
  getDemoStatus: () => authFetch(`${BASE}/demo/status`).then(r => r.json()),
  getEvents: (limit = 50) => authFetch(`${BASE}/events/?limit=${limit}`).then(r => r.json()),
  getEventChain: (correlationId: string) =>
    authFetch(`${BASE}/events/chain?correlation_id=${correlationId}`).then(r => r.json()),
  simulateLowStock: () => authFetch(`${BASE}/offline/simulate-low-stock`, { method: 'POST' }).then(r => r.json()),
  simulateCloudDown: () => authFetch(`${BASE}/offline/simulate-cloud-down`, { method: 'POST' }).then(r => r.json()),
  simulateCloudUp: () => authFetch(`${BASE}/offline/simulate-cloud-up`, { method: 'POST' }).then(r => r.json()),
  replay: () => authFetch(`${BASE}/offline/replay`, { method: 'POST' }).then(r => r.json()),
  generatePO: () => authFetch(`${BASE}/erp/generate-purchase-order`, { method: 'POST' }).then(r => r.json()),
  detectIdle: () => authFetch(`${BASE}/production/detect-idle`, { method: 'POST' }).then(r => r.json()),
  bufferStatus: () => authFetch(`${BASE}/offline/buffer-status`).then(r => r.json()),
  getStockHistory: () => authFetch(`${BASE}/erp/stock-history`).then(r => r.json()),
  getInferenceStatus: () => authFetch(`${BASE}/aiml/inference-status`).then(r => r.json()),
  runOfflineNarrative: () =>
    authFetch(`${BASE}/demo/run-offline-narrative`, { method: 'POST' }).then(r => r.json()),
  getActiveRecommendation: () => authFetch(`${BASE}/recommendations/active`).then(r => r.json()),
  getRecommendations: () => authFetch(`${BASE}/recommendations/`).then(r => r.json()),
  approveRecommendation: (recommendationId: string, comment?: string) =>
    authFetch(`${BASE}/recommendations/${recommendationId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: 'PA-OPERADOR', comment }),
    }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo aprobar la recomendacion')
      return json
    }),
  rejectRecommendation: (recommendationId: string, comment: string) =>
    authFetch(`${BASE}/recommendations/${recommendationId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: 'PA-OPERADOR', comment }),
    }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo rechazar la recomendacion')
      return json
    }),
  getPurchaseOrders: () => authFetch(`${BASE}/purchase-orders/`).then(r => r.json()),
  getSuppliers: (skuId = 'SKU-ACERO-M8') =>
    authFetch(`${BASE}/purchase-orders/suppliers?sku_id=${encodeURIComponent(skuId)}`).then(r => r.json()),
  updatePurchaseOrder: (
    poId: string,
    payload: { supplier_id?: string; quantity_units?: number; required_date?: string; comment?: string },
  ) =>
    authFetch(`${BASE}/purchase-orders/${poId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo actualizar la orden')
      return json
    }),
  approvePurchaseOrder: (poId: string, comment?: string) =>
    authFetch(`${BASE}/purchase-orders/${poId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: 'PA-OPERADOR', comment }),
    }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo aprobar la orden')
      return json
    }),
  getSupplierRecommendation: (skuId = 'SKU-ACERO-M8', strategy: 'urgency' | 'cost' = 'urgency') =>
    authFetch(`${BASE}/suppliers/recommended?sku_id=${encodeURIComponent(skuId)}&strategy=${strategy}`).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo recomendar proveedor')
      return json
    }),
  createSupplier: (payload: {
    supplier_id?: string
    name: string
    sku_ids: string[]
    lead_time_days: number
    unit_cost_mxn: number
    reliability_score: number
    minimum_order_quantity: number
  }) =>
    authFetch(`${BASE}/suppliers/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo crear proveedor')
      return json
    }),
  updateSupplier: (
    supplierId: string,
    payload: {
      name?: string
      sku_ids?: string[]
      lead_time_days?: number
      unit_cost_mxn?: number
      reliability_score?: number
      minimum_order_quantity?: number
    },
  ) =>
    authFetch(`${BASE}/suppliers/${supplierId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo actualizar proveedor')
      return json
    }),
  deleteSupplier: (supplierId: string) =>
    authFetch(`${BASE}/suppliers/${supplierId}`, { method: 'DELETE' }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo eliminar proveedor')
      return json
    }),
  getMaterials: (status?: 'critical' | 'low_stock' | 'normal') => {
    const query = status ? `?status=${status}` : ''
    return authFetch(`${BASE}/materials/${query}`).then(r => r.json())
  },
  updateMaterial: (
    skuId: string,
    payload: {
      current_stock_units?: number
      reorder_point_units?: number
      daily_demand_units?: number
      unit_cost_mxn?: number
      criticality?: string
    },
  ) =>
    authFetch(`${BASE}/materials/${encodeURIComponent(skuId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo actualizar material')
      return json
    }),
  createMaterialRecommendation: (skuId: string) =>
    authFetch(`${BASE}/materials/${encodeURIComponent(skuId)}/recommendation`, { method: 'POST' }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo generar recomendacion')
      return json
    }),
  getProductionBacklog: () => authFetch(`${BASE}/production/backlog`).then(r => r.json()),
  getBacklogSuggestion: () => authFetch(`${BASE}/production/backlog/suggestion`).then(r => r.json()),
  resequenceBacklog: (comment?: string) =>
    authFetch(`${BASE}/production/backlog/resequence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: 'PA-OPERADOR', comment }),
    }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo reprogramar backlog')
      return json
    }),
  updateProductionJob: (
    jobId: string,
    payload: { priority?: number; sequence?: number; status?: string; required_start?: string },
  ) =>
    authFetch(`${BASE}/production/backlog/${encodeURIComponent(jobId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(async r => {
      const json = await r.json()
      if (!r.ok) throw new Error(json.detail ?? 'No se pudo actualizar job')
      return json
    }),
  getAudit: (params: {
    entity_type?: string
    entity_id?: string
    sku_id?: string
    correlation_id?: string
    limit?: number
  } = {}) => {
    const search = new URLSearchParams()
    if (params.entity_type) search.set('entity_type', params.entity_type)
    if (params.entity_id) search.set('entity_id', params.entity_id)
    if (params.sku_id) search.set('sku_id', params.sku_id)
    if (params.correlation_id) search.set('correlation_id', params.correlation_id)
    if (params.limit) search.set('limit', String(params.limit))
    const query = search.toString()
    return authFetch(`${BASE}/audit/${query ? `?${query}` : ''}`).then(r => r.json())
  },
  exportAudit: (params: {
    format: 'json' | 'csv'
    entity_type?: string
    entity_id?: string
    sku_id?: string
    correlation_id?: string
  }) => authFetch(auditExportUrl(params)).then(async r => {
    if (!r.ok) {
      const json = await r.json()
      throw new Error(json.detail ?? 'No se pudo exportar auditoria')
    }
    return r.blob()
  }),
}

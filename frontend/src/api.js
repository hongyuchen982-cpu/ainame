const API_BASE = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')

const getSession = () => {
  try { return JSON.parse(localStorage.getItem('qiming_session') || 'null') } catch { return null }
}

const saveSession = (session) => {
  if (session) localStorage.setItem('qiming_session', JSON.stringify(session))
  else localStorage.removeItem('qiming_session')
  window.dispatchEvent(new Event('session-change'))
}

async function parseResponse(response) {
  const type = response.headers.get('content-type') || ''
  const body = type.includes('application/json') ? await response.json() : await response.text()
  if (!response.ok) {
    const detail = body?.detail
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg).join('；')
      : detail || body?.message || body || `请求失败 (${response.status})`
    const error = new Error(message)
    error.status = response.status
    throw error
  }
  return body
}

async function request(path, options = {}, retry = true) {
  const session = getSession()
  const headers = new Headers(options.headers || {})
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (session?.access_token && options.auth !== false) {
    headers.set('Authorization', `Bearer ${session.access_token}`)
  }
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (response.status === 401 && retry && session?.refresh_token) {
    try {
      const refreshed = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST', headers: { Authorization: `Bearer ${session.refresh_token}` },
      }).then(parseResponse)
      saveSession({ ...session, access_token: refreshed.access_token })
      return request(path, options, false)
    } catch {
      saveSession(null)
    }
  }
  return parseResponse(response)
}

export const api = {
  getSession,
  saveSession,
  sendCode: (email) => request(`/auth/code?email=${encodeURIComponent(email)}`, { auth: false }),
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data), auth: false }),
  login: (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data), auth: false }),
  balance: () => request('/credit/balance'),
  generateNames: (data) => request('/name/generate', { method: 'POST', body: JSON.stringify(data) }),
  feedbackNames: (data) => request('/name/feedback', { method: 'POST', body: JSON.stringify(data) }),
  uploadKnowledge: (file) => {
    const body = new FormData(); body.append('file', file)
    return request('/knowledge/upload', { method: 'POST', body })
  },
  generateLogo: (data) => request('/logos/generate', { method: 'POST', body: JSON.stringify(data), auth: false }),
  packages: () => request('/package/list', { auth: false }),
  createOrder: (package_id) => request('/pay/create_order', { method: 'POST', body: JSON.stringify({ package_id }) }),
  order: (orderNo) => request(`/pay/order/${orderNo}`),
}

export function resolveAssetUrl(url) {
  if (!url || /^https?:\/\//.test(url)) return url
  if (url.startsWith('/static')) return url
  return `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}`
}

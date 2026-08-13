import { API_BASE, SESSION_KEY } from './config'

let refreshTask = null
export const getSession = () => uni.getStorageSync(SESSION_KEY) || null
export const saveSession = (value) => value ? uni.setStorageSync(SESSION_KEY, value) : uni.removeStorageSync(SESSION_KEY)

function requestRaw(url, options = {}) {
  return new Promise((resolve, reject) => uni.request({
    url: `${API_BASE}${url}`, method: options.method || 'GET', data: options.data,
    header: options.header, timeout: 30000, success: resolve, fail: reject,
  }))
}
function responseError(response) {
  const detail = response?.data?.detail
  const message = Array.isArray(detail) ? detail.map((item) => item.msg).join('；') : detail || response?.data?.message || `请求失败 (${response?.statusCode || '网络异常'})`
  const error = new Error(message); error.status = response?.statusCode; return error
}
async function refresh(session) {
  if (!refreshTask) refreshTask = requestRaw('/auth/refresh', { method: 'POST', header: { Authorization: `Bearer ${session.refresh_token}` } })
    .then((response) => { if (response.statusCode < 200 || response.statusCode >= 300) throw responseError(response); const next = { ...session, ...response.data, user: session.user }; saveSession(next); return next })
    .finally(() => { refreshTask = null })
  return refreshTask
}
export async function request(url, options = {}, retry = true) {
  const session = getSession(), header = { ...(options.header || {}) }
  if (session?.access_token && options.auth !== false) header.Authorization = `Bearer ${session.access_token}`
  const response = await requestRaw(url, { ...options, header })
  if (response.statusCode === 401 && retry && session?.refresh_token) {
    try { await refresh(session); return request(url, options, false) }
    catch (error) { saveSession(null); throw error }
  }
  if (response.statusCode < 200 || response.statusCode >= 300) throw responseError(response)
  return response.data
}
export function uploadKnowledge(filePath) {
  const session = getSession()
  return new Promise((resolve, reject) => uni.uploadFile({
    url: `${API_BASE}/knowledge/upload`, filePath, name: 'file',
    header: session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {},
    success(response) { let data = response.data; try { data = JSON.parse(data) } catch {} response.statusCode >= 200 && response.statusCode < 300 ? resolve(data) : reject(responseError({ ...response, data })) },
    fail: reject,
  }))
}
export const api = {
  login: (data) => request('/auth/login', { method: 'POST', data, auth: false }), logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/users/me'), dashboard: () => request('/users/me/dashboard'), balance: () => request('/credit/balance'),
  knowledgeFiles: () => request('/knowledge/files'), reprocessKnowledge: (id) => request(`/knowledge/files/${id}/reprocess`, { method: 'POST' }), deleteKnowledge: (id) => request(`/knowledge/files/${id}`, { method: 'DELETE' }),
  tasks: () => request('/tasks'), retryTask: (id) => request(`/tasks/${id}/retry`, { method: 'POST' }),
  expertPackages: () => request('/experts/packages', { auth: false }), expertProfile: () => request('/experts/me'), expertOrders: () => request('/experts/orders'), projects: () => request('/projects'), applyExpert: (data) => request('/experts/apply', { method: 'POST', data }),
  developerAccount: () => request('/developers/account'), apiPlans: () => request('/developers/plans'), subscriptions: () => request('/developers/subscriptions'), usageSummary: () => request('/developers/usage/summary'), createDeveloperAccount: (data) => request('/developers/account', { method: 'POST', data }),
}
export function requireLogin() { if (getSession()) return true; uni.reLaunch({ url: '/pages/login/login' }); return false }

const API_BASE = (import.meta.env.VITE_API_BASE || '/api').replace(/\/$/, '')
let refreshPromise = null

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

async function refreshSession(session) {
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST', headers: { Authorization: `Bearer ${session.refresh_token}` },
    })
      .then(parseResponse)
      .then((refreshed) => {
        const latest = getSession() || session
        const next = {
          ...latest,
          access_token: refreshed.access_token,
          refresh_token: refreshed.refresh_token,
        }
        saveSession(next)
        return next
      })
      .finally(() => { refreshPromise = null })
  }
  return refreshPromise
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
      await refreshSession(session)
      return request(path, options, false)
    } catch {
      if (getSession()?.refresh_token === session.refresh_token) saveSession(null)
    }
  }
  return parseResponse(response)
}

async function downloadFile(path, filename, retry = true) {
  const session = getSession()
  const headers = new Headers()
  if (session?.access_token) headers.set('Authorization', `Bearer ${session.access_token}`)
  const response = await fetch(`${API_BASE}${path}`, { headers })
  if (response.status === 401 && retry && session?.refresh_token) {
    await refreshSession(session)
    return downloadFile(path, filename, false)
  }
  if (!response.ok) return parseResponse(response)
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(url)
}

export const api = {
  getSession,
  saveSession,
  sendCode: (email) => request(`/auth/code?email=${encodeURIComponent(email)}`, { auth: false }),
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data), auth: false }),
  login: (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data), auth: false }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  sendPasswordResetCode: (email) => request('/auth/password-reset/code', { method: 'POST', body: JSON.stringify({ email }), auth: false }),
  resetPassword: (data) => request('/auth/password-reset/confirm', { method: 'POST', body: JSON.stringify(data), auth: false }),
  me: () => request('/users/me'),
  dashboard: () => request('/users/me/dashboard'),
  updateProfile: (data) => request('/users/me', { method: 'PATCH', body: JSON.stringify(data) }),
  uploadAvatar: (file) => { const body = new FormData(); body.append('file', file); return request('/users/me/avatar', { method: 'POST', body }) },
  changePassword: (data) => request('/users/me/password', { method: 'POST', body: JSON.stringify(data) }),
  devices: () => request('/users/me/devices'),
  revokeDevice: (deviceId) => request(`/users/me/devices/${deviceId}`, { method: 'DELETE' }),
  loginRecords: () => request('/users/me/login-records'),
  balance: () => request('/credit/balance'),
  creditAccount: () => request('/credit/account'),
  creditLogs: () => request('/credit/logs'),
  adminCreditAccounts: () => request('/admin/credits'),
  adminDashboard: () => request('/admin/dashboard'),
  adminUsers: () => request('/admin/users'),
  adminUpdateUserStatus: (id, status) => request(`/admin/users/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  adminRoles: () => request('/admin/roles'),
  adminPermissions: () => request('/admin/permissions'),
  adminCreateRole: (data) => request('/admin/roles', { method: 'POST', body: JSON.stringify(data) }),
  adminUpdateRolePermissions: (code, permissions) => request(`/admin/roles/${encodeURIComponent(code)}/permissions`, { method: 'PUT', body: JSON.stringify({ permissions }) }),
  adminUpdateUserRoles: (id, roles) => request(`/admin/users/${id}/roles`, { method: 'PUT', body: JSON.stringify({ roles }) }),
  adminAuditLogs: () => request('/admin/audit-logs'),
  adminProjects: (status = '') => request(`/admin/projects${status ? `?status=${encodeURIComponent(status)}` : ''}`),
  adjustCredit: (userId, data) => request(`/admin/users/${userId}/credits`, { method: 'POST', body: JSON.stringify(data) }),
  generateNames: (data) => request('/name/generate', { method: 'POST', body: JSON.stringify(data) }),
  feedbackNames: (data) => request('/name/feedback', { method: 'POST', body: JSON.stringify(data) }),
  selectName: (data) => request('/name/select', { method: 'POST', body: JSON.stringify(data) }),
  selectedName: (selectionId) => request(`/name/selections/${selectionId}`),
  selectedNames: () => request('/name/selections'),
  validations: (selectedNameId = '') => request(`/validations${selectedNameId ? `?selected_name_id=${selectedNameId}` : ''}`),
  validation: (id) => request(`/validations/${id}`),
  createValidation: (data) => request('/validations', { method: 'POST', body: JSON.stringify(data) }),
  adminValidations: (risk = '') => request(`/admin/validations${risk ? `?risk_level=${encodeURIComponent(risk)}` : ''}`),
  brandAssets: (selectedNameId = '') => request(`/brand-assets${selectedNameId ? `?selected_name_id=${selectedNameId}` : ''}`),
  brandAsset: (id) => request(`/brand-assets/${id}`),
  createBrandAsset: (data) => request('/brand-assets', { method: 'POST', body: JSON.stringify(data) }),
  adminBrandAssets: () => request('/admin/brand-assets'),
  reports: () => request('/reports'),
  report: (id) => request(`/reports/${id}`),
  createReport: (data) => request('/reports', { method: 'POST', body: JSON.stringify(data) }),
  downloadReport: (id, filename = `naming-report-${id}.pdf`) => downloadFile(`/reports/${id}/download`, filename),
  adminReports: () => request('/admin/reports'),
  adminDownloadReport: (id, filename = `naming-report-${id}.pdf`) => downloadFile(`/admin/reports/${id}/download`, filename),
  projects: (status = '') => request(`/projects${status ? `?status=${encodeURIComponent(status)}` : ''}`),
  project: (projectId) => request(`/projects/${projectId}`),
  createProject: (data) => request('/projects', { method: 'POST', body: JSON.stringify(data) }),
  updateProject: (projectId, data) => request(`/projects/${projectId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  archiveProject: (projectId) => request(`/projects/${projectId}/archive`, { method: 'POST' }),
  restoreProject: (projectId) => request(`/projects/${projectId}/restore`, { method: 'POST' }),
  uploadKnowledge: (file) => {
    const body = new FormData(); body.append('file', file)
    return request('/knowledge/upload', { method: 'POST', body })
  },
  knowledgeFiles: () => request('/knowledge/files'),
  reprocessKnowledge: (id) => request(`/knowledge/files/${id}/reprocess`, { method: 'POST' }),
  deleteKnowledge: (id) => request(`/knowledge/files/${id}`, { method: 'DELETE' }),
  adminKnowledgeFiles: (status = '') => request(`/admin/knowledge/files${status ? `?status=${encodeURIComponent(status)}` : ''}`),
  adminReprocessKnowledge: (id) => request(`/admin/knowledge/files/${id}/reprocess`, { method: 'POST' }),
  adminDeleteKnowledge: (id) => request(`/admin/knowledge/files/${id}`, { method: 'DELETE' }),
  tasks: (status = '') => request(`/tasks${status ? `?status=${encodeURIComponent(status)}` : ''}`),
  task: (id) => request(`/tasks/${id}`),
  retryTask: (id) => request(`/tasks/${id}/retry`, { method: 'POST' }),
  adminTasks: (status = '') => request(`/admin/tasks${status ? `?status=${encodeURIComponent(status)}` : ''}`),
  adminRetryTask: (id) => request(`/admin/tasks/${id}/retry`, { method: 'POST' }),
  adminCancelTask: (id) => request(`/admin/tasks/${id}/cancel`, { method: 'POST' }),
  generateLogo: (data) => request('/logos/generate', { method: 'POST', body: JSON.stringify(data) }),
  packages: () => request('/package/list', { auth: false }),
  adminPackages: () => request('/admin/packages'),
  createPackage: (data) => request('/admin/packages', { method: 'POST', body: JSON.stringify(data) }),
  updatePackage: (id, data) => request(`/admin/packages/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  setPackageStatus: (id, is_active) => request(`/admin/packages/${id}/status`, { method: 'POST', body: JSON.stringify({ is_active }) }),
  sortPackages: (items) => request('/admin/packages/sort', { method: 'PUT', body: JSON.stringify({ items }) }),
  deletePackage: (id) => request(`/admin/packages/${id}`, { method: 'DELETE' }),
  createOrder: (package_id, client_request_id) => request('/pay/create_order', { method: 'POST', body: JSON.stringify({ package_id, client_request_id }) }),
  order: (orderNo) => request(`/pay/order/${orderNo}`),
  orders: () => request('/pay/orders'),
  orderDetail: (orderNo) => request(`/pay/orders/${orderNo}/detail`),
  syncOrder: (orderNo) => request(`/pay/orders/${orderNo}/sync`, { method: 'POST' }),
  continueOrderPayment: (orderNo) => request(`/pay/orders/${orderNo}/pay`, { method: 'POST' }),
  closeOrder: (orderNo) => request(`/pay/orders/${orderNo}/close`, { method: 'POST' }),
  adminOrders: (status = '') => request(`/admin/orders${status ? `?status=${encodeURIComponent(status)}` : ''}`),
  adminOrderDetail: (orderNo) => request(`/admin/orders/${encodeURIComponent(orderNo)}`),
  refundOrder: (orderNo, data) => request(`/admin/orders/${orderNo}/refund`, { method: 'POST', body: JSON.stringify(data) }),
  adminCloseOrder: (orderNo) => request(`/admin/orders/${orderNo}/close`, { method: 'POST' }),
  expertProfile: () => request('/experts/me'),
  applyExpert: (data) => request('/experts/apply', { method: 'POST', body: JSON.stringify(data) }),
  expertPackages: () => request('/experts/packages', { auth: false }),
  createExpertOrder: (data) => request('/experts/orders', { method: 'POST', body: JSON.stringify(data) }),
  expertCustomerOrders: () => request('/experts/orders'),
  reviewExpertOrder: (id, data) => request(`/experts/orders/${id}/review`, { method: 'POST', body: JSON.stringify(data) }),
  ownExpertPackages: () => request('/expert/packages'),
  createExpertPackage: (data) => request('/expert/packages', { method: 'POST', body: JSON.stringify(data) }),
  setExpertPackageStatus: (id, is_active) => request(`/expert/packages/${id}/status`, { method: 'POST', body: JSON.stringify({ is_active }) }),
  expertWorkOrders: () => request('/expert/orders'),
  acceptExpertOrder: (id) => request(`/expert/orders/${id}/accept`, { method: 'POST' }),
  deliverExpertOrder: (id, data) => request(`/expert/orders/${id}/deliver`, { method: 'POST', body: JSON.stringify(data) }),
  expertSettlements: () => request('/expert/settlements'),
  adminExpertApplications: (status = '') => request(`/admin/experts/applications${status ? `?status=${encodeURIComponent(status)}` : ''}`),
  adminReviewExpert: (id, data) => request(`/admin/experts/applications/${id}/review`, { method: 'POST', body: JSON.stringify(data) }),
  adminExpertOrders: () => request('/admin/experts/orders'),
  adminExpertSettlements: () => request('/admin/experts/settlements'),
  adminSettleExpert: (id) => request(`/admin/experts/settlements/${id}/settle`, { method: 'POST' }),
  communityPolls: (query = '') => request(`/community/polls${query ? `?${query}` : ''}`),
  communityPoll: (id) => request(`/community/polls/${id}`),
  createCommunityPoll: (data) => request('/community/polls', { method: 'POST', body: JSON.stringify(data) }),
  voteCommunityPoll: (id, candidate_id) => request(`/community/polls/${id}/vote`, { method: 'POST', body: JSON.stringify({ candidate_id }) }),
  commentCommunityPoll: (id, content) => request(`/community/polls/${id}/comments`, { method: 'POST', body: JSON.stringify({ content }) }),
  closeCommunityPoll: (id) => request(`/community/polls/${id}/close`, { method: 'POST' }),
  reportCommunityContent: (data) => request('/community/reports', { method: 'POST', body: JSON.stringify(data) }),
  adminCommunityReports: (status = '') => request(`/admin/community/reports${status ? `?status=${encodeURIComponent(status)}` : ''}`),
  featureCommunityPoll: (id, is_featured) => request(`/admin/community/polls/${id}/featured`, { method: 'POST', body: JSON.stringify({ is_featured }) }),
  moderateCommunityReport: (id, data) => request(`/admin/community/reports/${id}/moderate`, { method: 'POST', body: JSON.stringify(data) }),
  developerAccount: () => request('/developers/account'),
  createDeveloperAccount: (data) => request('/developers/account', { method: 'POST', body: JSON.stringify(data) }),
  developerKeys: () => request('/developers/keys'),
  createDeveloperKey: (name) => request('/developers/keys', { method: 'POST', body: JSON.stringify({ name }) }),
  revokeDeveloperKey: (id) => request(`/developers/keys/${id}`, { method: 'DELETE' }),
  apiPlans: () => request('/developers/plans'),
  subscribeApiPlan: (id) => request(`/developers/plans/${id}/subscribe`, { method: 'POST' }),
  apiSubscriptions: () => request('/developers/subscriptions'),
  apiUsage: () => request('/developers/usage'),
  apiUsageSummary: () => request('/developers/usage/summary'),
  adminDevelopers: () => request('/admin/developers'),
  createApiPlan: (data) => request('/admin/developers/plans', { method: 'POST', body: JSON.stringify(data) }),
  grantApiPlan: (developerId, plan_id) => request(`/admin/developers/${developerId}/grant`, { method: 'POST', body: JSON.stringify({ plan_id }) }),
  setDeveloperStatus: (developerId, status) => request(`/admin/developers/${developerId}/status`, { method: 'POST', body: JSON.stringify({ status }) }),
  growthPromotion: () => request('/growth/promotion'),
  growthReferrals: () => request('/growth/referrals'),
  growthRewards: () => request('/growth/rewards'),
  growthCommissions: () => request('/growth/commissions'),
  growthCampaigns: () => request('/admin/growth/campaigns'),
  createGrowthCampaign: (data) => request('/admin/growth/campaigns', { method: 'POST', body: JSON.stringify(data) }),
  setGrowthCampaignStatus: (id, is_active) => request(`/admin/growth/campaigns/${id}/status`, { method: 'POST', body: JSON.stringify({ is_active }) }),
  adminGrowthCommissions: () => request('/admin/growth/commissions'),
}

export function resolveAssetUrl(url) {
  if (!url || /^https?:\/\//.test(url)) return url
  if (url.startsWith('/static')) return url
  return `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}`
}

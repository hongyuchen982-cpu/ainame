export function hasPermission(user, permission) {
  return Boolean(user?.roles?.includes('admin') || user?.permissions?.includes(permission))
}

export const OPERATIONS_ROUTES = [
  ['admin-users', 'users.read'],
  ['admin-security', 'roles.manage'],
  ['admin-credits', 'credits.manage'],
  ['admin-packages', 'packages.manage'],
  ['admin-orders', 'orders.manage'],
  ['admin-projects', 'projects.manage'],
  ['admin-validations', 'validations.manage'],
  ['admin-brand-assets', 'brand_assets.manage'],
  ['admin-reports', 'reports.manage'],
  ['admin-knowledge', 'knowledge.manage'],
  ['admin-tasks', 'tasks.manage'],
  ['admin-experts', 'experts.manage'],
  ['admin-community', 'community.moderate'],
  ['admin-developers', 'developers.manage'],
  ['admin-growth', 'growth.manage'],
]

export function operationsRoute(user) {
  if (hasPermission(user, 'dashboard.read')) return 'admin-dashboard'
  if (hasPermission(user, 'audit.read')) return 'admin-security'
  return OPERATIONS_ROUTES.find((item) => hasPermission(user, item[1]))?.[0] || ''
}

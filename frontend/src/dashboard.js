export const USER_CENTER_MODULES = [
  { id: 'account', label: '我的资料', countKey: null },
  { id: 'credits', label: '我的次数', countKey: 'credit_balance' },
  { id: 'credits', label: '次数流水', countKey: 'credit_logs' },
  { id: 'projects', label: '我的命名项目', countKey: 'projects_total' },
  { id: 'orders', label: '我的订单', countKey: 'orders_total' },
  { id: 'knowledge', label: '我的知识库', countKey: 'knowledge_files' },
  { id: 'reports', label: '报告下载', countKey: 'reports_total' },
]

export function getPrimaryDashboardAction(dashboard = {}) {
  if (!dashboard.projects_total) {
    return { page: 'create', label: '开始第一个命名项目' }
  }
  if (!dashboard.projects_selected) {
    return { page: 'projects', label: '继续项目并选定名称' }
  }
  if (!dashboard.reports_total) {
    return { page: 'reports', label: '生成第一份命名报告' }
  }
  return { page: 'projects', label: '继续管理命名项目' }
}

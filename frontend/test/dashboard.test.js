import test from 'node:test'
import assert from 'node:assert/strict'

import { getPrimaryDashboardAction, USER_CENTER_MODULES } from '../src/dashboard.js'

test('user center exposes the seven requested modules', () => {
  assert.deepEqual(USER_CENTER_MODULES.map((item) => item.label), [
    '我的资料', '我的次数', '次数流水', '我的命名项目', '我的订单', '我的知识库', '报告下载',
  ])
})

test('dashboard action follows the naming journey', () => {
  assert.equal(getPrimaryDashboardAction({}).page, 'create')
  assert.equal(getPrimaryDashboardAction({ projects_total: 1 }).page, 'projects')
  assert.equal(getPrimaryDashboardAction({ projects_total: 1, projects_selected: 1 }).page, 'reports')
  assert.equal(getPrimaryDashboardAction({ projects_total: 1, projects_selected: 1, reports_total: 1 }).page, 'projects')
})

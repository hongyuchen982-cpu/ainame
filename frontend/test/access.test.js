import test from 'node:test'
import assert from 'node:assert/strict'

import { hasPermission, operationsRoute } from '../src/access.js'

test('admin role keeps full backward-compatible access', () => {
  const user = { roles: ['admin'], permissions: [] }
  assert.equal(hasPermission(user, 'orders.manage'), true)
  assert.equal(operationsRoute(user), 'admin-dashboard')
})

test('custom roles enter only the operations module granted by permissions', () => {
  assert.equal(operationsRoute({ roles: ['operator'], permissions: ['users.read'] }), 'admin-users')
  assert.equal(operationsRoute({ roles: ['auditor'], permissions: ['audit.read'] }), 'admin-security')
  assert.equal(hasPermission({ roles: ['member'], permissions: [] }, 'users.read'), false)
})

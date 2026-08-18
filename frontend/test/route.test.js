import test from 'node:test'
import assert from 'node:assert/strict'

import {
  categoryFromPreset,
  normalizeCreatePreset,
  parseHash,
  safeDecodeRouteValue,
} from '../src/route.js'

test('parses regular encoded routes', () => {
  assert.deepEqual(parseHash('#create/%E4%BC%81%E4%B8%9A%E5%90%8D'), {
    page: 'create',
    value: '企业名',
  })
  assert.deepEqual(parseHash('#projects/42'), { page: 'projects', value: '42' })
})

test('parses user and admin knowledge routes', () => {
  assert.deepEqual(parseHash('#knowledge'), { page: 'knowledge', value: '' })
  assert.deepEqual(parseHash('#admin-knowledge'), { page: 'admin-knowledge', value: '' })
})

test('parses user and admin async task routes', () => {
  assert.deepEqual(parseHash('#tasks'), { page: 'tasks', value: '' })
  assert.deepEqual(parseHash('#admin-tasks'), { page: 'admin-tasks', value: '' })
})

test('parses name validation routes', () => {
  assert.deepEqual(parseHash('#validation/42'), { page: 'validation', value: '42' })
  assert.deepEqual(parseHash('#admin-validations'), { page: 'admin-validations', value: '' })
})

test('parses user and admin brand asset routes', () => {
  assert.deepEqual(parseHash('#brand-assets/42'), { page: 'brand-assets', value: '42' })
  assert.deepEqual(parseHash('#admin-brand-assets'), { page: 'admin-brand-assets', value: '' })
})

test('parses user and admin PDF report routes', () => {
  assert.deepEqual(parseHash('#reports'), { page: 'reports', value: '' })
  assert.deepEqual(parseHash('#admin-reports'), { page: 'admin-reports', value: '' })
})

test('parses operations dashboard and project routes', () => {
  assert.deepEqual(parseHash('#admin-dashboard'), { page: 'admin-dashboard', value: '' })
  assert.deepEqual(parseHash('#admin-users'), { page: 'admin-users', value: '' })
  assert.deepEqual(parseHash('#admin-projects'), { page: 'admin-projects', value: '' })
  assert.deepEqual(parseHash('#admin-security'), { page: 'admin-security', value: '' })
})

test('parses expert service routes', () => {
  assert.deepEqual(parseHash('#experts'), { page: 'experts', value: '' })
  assert.deepEqual(parseHash('#expert-workspace'), { page: 'expert-workspace', value: '' })
  assert.deepEqual(parseHash('#admin-experts'), { page: 'admin-experts', value: '' })
})

test('parses community crowdsourcing routes', () => {
  assert.deepEqual(parseHash('#community'), { page: 'community', value: '' })
  assert.deepEqual(parseHash('#community-publish'), { page: 'community-publish', value: '' })
  assert.deepEqual(parseHash('#community-detail/9'), { page: 'community-detail', value: '9' })
  assert.deepEqual(parseHash('#admin-community'), { page: 'admin-community', value: '' })
})

test('parses developer platform routes', () => {
  assert.deepEqual(parseHash('#developers'), { page: 'developers', value: '' })
  assert.deepEqual(parseHash('#admin-developers'), { page: 'admin-developers', value: '' })
})

test('parses growth and distribution routes', () => {
  assert.deepEqual(parseHash('#growth'), { page: 'growth', value: '' })
  assert.deepEqual(parseHash('#register/ABCD1234'), { page: 'register', value: 'ABCD1234' })
  assert.deepEqual(parseHash('#admin-growth'), { page: 'admin-growth', value: '' })
})

test('malformed URL encoding never crashes route parsing', () => {
  assert.equal(safeDecodeRouteValue('%'), '')
  assert.deepEqual(parseHash('#create/%E0%A4%A'), { page: 'create', value: '' })
})

test('invalid create presets fall back to a supported category', () => {
  assert.equal(normalizeCreatePreset('错误类型'), '')
  assert.equal(normalizeCreatePreset('project:not-a-number'), '')
  assert.equal(categoryFromPreset('错误类型'), '人名')
  assert.equal(categoryFromPreset('企业名'), '企业名')
  assert.equal(normalizeCreatePreset('project:17'), 'project:17')
})

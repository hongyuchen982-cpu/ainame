import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'

const appSource = readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8')

test('effects never return page-loading promises as cleanup functions', () => {
  assert.doesNotMatch(appSource, /useEffect\(\s*load\s*,/)
  assert.doesNotMatch(appSource, /useEffect\(\s*async\s*/)
})

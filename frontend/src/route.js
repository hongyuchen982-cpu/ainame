export const NAMING_CATEGORIES = ['人名', '企业名', '宠物名']

export function safeDecodeRouteValue(value = '') {
  try {
    return decodeURIComponent(value)
  } catch {
    return ''
  }
}

export function parseHash(hash = '') {
  const raw = String(hash).replace(/^#/, '')
  const separator = raw.indexOf('/')
  const page = separator < 0 ? raw : raw.slice(0, separator)
  const encodedValue = separator < 0 ? '' : raw.slice(separator + 1)
  return {
    page: page || 'home',
    value: safeDecodeRouteValue(encodedValue),
  }
}

export function normalizeCreatePreset(value = '') {
  if (NAMING_CATEGORIES.includes(value)) return value
  if (value.startsWith('project:')) {
    const id = Number(value.slice(8))
    return Number.isSafeInteger(id) && id > 0 ? `project:${id}` : ''
  }
  return ''
}

export function categoryFromPreset(value = '') {
  const normalized = normalizeCreatePreset(value)
  return NAMING_CATEGORIES.includes(normalized) ? normalized : '人名'
}

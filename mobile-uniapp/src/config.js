const envBase = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')
let defaultBase = '/api'
// #ifdef APP-PLUS
defaultBase = 'http://192.168.31.211:8000'
// #endif
export const API_BASE = envBase || defaultBase
export const SESSION_KEY = 'qiming_mobile_session'

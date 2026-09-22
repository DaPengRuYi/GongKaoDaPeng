// 在线刷题相关后端接口封装
// 对应后端 /api/quiz 路由，字段名与后端 API 契约严格对齐。
const BASE = '/api/quiz'

/**
 * 随机抽取若干道题。
 * @param {{subject?: string, module?: string, n?: number}} params
 * @returns {Promise<{items: Array<object>, graded_available: boolean}>}
 */
export async function fetchRandom({ subject = '', module = '', n = 10 } = {}) {
  const params = new URLSearchParams()
  if (subject) params.set('subject', subject)
  if (module) params.set('module', module)
  params.set('n', String(n))
  const res = await fetch(`${BASE}/random?${params.toString()}`)
  if (!res.ok) throw new Error(`网络错误: ${res.status}`)
  return res.json()
}

/**
 * 提交单题答案并获取判分结果。
 * @param {{question_id: number, chosen: string, user_id?: number|null, time_sec?: number}} payload
 * @returns {Promise<{question_id:number, chosen:string, correct:string, is_correct:boolean|null, analysis:string, graded:boolean}>}
 */
export async function submitAnswer(payload) {
  const body = {
    question_id: payload.question_id,
    chosen: payload.chosen,
    user_id: payload.user_id ?? null,
    time_sec: payload.time_sec ?? 0
  }
  const res = await fetch(`${BASE}/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  if (!res.ok) throw new Error(`网络错误: ${res.status}`)
  return res.json()
}

/**
 * 获取错题本。
 * @param {{user_id?: number|null, subject?: string, module?: string, limit?: number}} params
 * @returns {Promise<{items: Array<object>}>}
 */
export async function fetchWrong({ user_id = null, subject = '', module = '', limit = 50 } = {}) {
  const params = new URLSearchParams()
  if (user_id != null) params.set('user_id', String(user_id))
  if (subject) params.set('subject', subject)
  if (module) params.set('module', module)
  params.set('limit', String(limit))
  const res = await fetch(`${BASE}/wrong?${params.toString()}`)
  if (!res.ok) throw new Error(`网络错误: ${res.status}`)
  return res.json()
}

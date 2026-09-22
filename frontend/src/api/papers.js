// 历年真题相关后端接口封装
// 对应后端 /api/papers 路由，字段名与后端 API 契约严格对齐。
const BASE = '/api/papers'

/**
 * 分页查询历年真题，支持科目 / 模块 / 年份筛选与关键字搜索。
 * @param {{subject?: string, module?: string, year?: string|number, q?: string, page?: number, page_size?: number}} params
 * @returns {Promise<{total:number, page:number, page_size:number, items:Array<object>, filters:{subjects:string[], modules:string[], years:number[]}}>}
 */
export async function fetchPapers({
  subject = '',
  module = '',
  year = '',
  q = '',
  page = 1,
  page_size = 20
} = {}) {
  const params = new URLSearchParams()
  if (subject) params.set('subject', subject)
  if (module) params.set('module', module)
  if (year !== '' && year != null) params.set('year', String(year))
  if (q) params.set('q', q)
  params.set('page', String(page))
  params.set('page_size', String(page_size))
  const res = await fetch(`${BASE}?${params.toString()}`)
  if (!res.ok) throw new Error(`网络错误: ${res.status}`)
  return res.json()
}

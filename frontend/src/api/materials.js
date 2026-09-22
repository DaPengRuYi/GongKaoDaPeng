// 学习资料相关后端接口封装
// 对应后端 /api/materials 路由，字段名与后端 API 契约严格对齐。
const BASE = '/api/materials'

/**
 * 获取某路径下的目录 / 文件列表，或按文件名关键字过滤。
 * @param {{path?: string, q?: string}} params
 * @returns {Promise<{root:string, path:string, entries:Array<{name:string, type:'dir'|'file', key:string, size:number|null}>}>}
 */
export async function fetchMaterials({ path = '', q = '' } = {}) {
  const params = new URLSearchParams()
  if (path) params.set('path', path)
  if (q) params.set('q', q)
  const res = await fetch(`${BASE}?${params.toString()}`)
  if (!res.ok) throw new Error(`网络错误: ${res.status}`)
  return res.json()
}

/**
 * 生成资料文件（PDF）的在线预览地址。
 * 后端以 FileResponse 流式返回，Content-Disposition 为 inline。
 * @param {string} key 文件 key（由后端返回）
 * @returns {string}
 */
export function materialFileUrl(key) {
  return `${BASE}/file?key=${encodeURIComponent(key)}`
}

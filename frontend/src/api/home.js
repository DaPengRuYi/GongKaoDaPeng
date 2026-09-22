// 首页数据接口
export async function fetchHome() {
  const res = await fetch('/api/home')
  if (!res.ok) throw new Error(`网络错误: ${res.status}`)
  return res.json()
}

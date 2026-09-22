<script setup>
import { ref, onMounted } from 'vue'
import { Folder, FileText, Search, Home as HomeIcon, ChevronRight } from 'lucide-vue-next'
import { fetchMaterials, materialFileUrl } from '../api/materials.js'

const path = ref('')
const q = ref('')
const root = ref('')
const entries = ref([])
const trail = ref([]) // 面包屑路径段：[{ name, key }]
const loading = ref(false)
const error = ref('')

/** 拉取当前路径下的目录 / 文件列表。 */
async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchMaterials({ path: path.value, q: q.value })
    root.value = data.root || ''
    path.value = data.path || ''
    entries.value = data.entries || []
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

/** 进入子目录（文件夹）。 */
function enterDir(entry) {
  path.value = entry.key
  trail.value.push({ name: entry.name, key: entry.key })
  load()
}

/** 打开文件：新标签页预览 PDF（后端 inline 流式返回）。 */
function openFile(key) {
  window.open(materialFileUrl(key), '_blank')
}

/** 回到根目录。 */
function goRoot() {
  path.value = ''
  trail.value = []
  load()
}

/** 点击面包屑某一段，回退到该层级。 */
function goTrail(index) {
  const seg = trail.value[index]
  if (!seg) return
  path.value = seg.key
  trail.value = trail.value.slice(0, index + 1)
  load()
}

function search() {
  load()
}

/** 人类可读的文件大小。 */
function formatSize(bytes) {
  if (bytes == null) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

onMounted(load)
</script>

<template>
  <div class="page">
    <h1 class="title">学习资料</h1>

    <div class="bar">
      <nav class="crumbs">
        <button class="crumb root" @click="goRoot">
          <HomeIcon :size="15" /> {{ root || '资料库' }}
        </button>
        <template v-for="(seg, i) in trail" :key="seg.key">
          <ChevronRight :size="14" class="sep" />
          <button class="crumb" @click="goTrail(i)">{{ seg.name }}</button>
        </template>
      </nav>
      <div class="search">
        <Search :size="16" />
        <input v-model="q" class="inp" placeholder="搜索文件名" @keyup.enter="search" />
      </div>
    </div>

    <p v-if="error" class="hint err">{{ error }}</p>
    <p v-if="loading" class="hint">加载中…</p>
    <p v-else-if="!entries.length" class="hint">暂无内容</p>

    <ul v-else class="list">
      <li
        v-for="e in entries"
        :key="e.key"
        class="entry"
        :class="e.type"
        @click="e.type === 'dir' ? enterDir(e) : openFile(e.key)"
      >
        <component :is="e.type === 'dir' ? Folder : FileText" :size="20" class="ic" />
        <span class="name">{{ e.name }}</span>
        <span v-if="e.size != null" class="size">{{ formatSize(e.size) }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 40px 24px 24px;
}
.title {
  font-size: 30px;
  font-weight: 800;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  margin-bottom: 22px;
}

.bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.crumbs {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  min-width: 0;
}
.crumb {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 14px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 8px;
}
.crumb:hover {
  color: var(--text);
  background: var(--bg-soft);
}
.crumb.root {
  color: var(--accent);
  font-weight: 600;
}
.sep {
  color: #4a5180;
}

.search {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--bg-soft);
  border: 1px solid #2a2f5e;
  border-radius: 10px;
  padding: 0 12px;
  color: var(--text-dim);
}
.search:focus-within {
  border-color: var(--accent);
}
.inp {
  background: transparent;
  border: none;
  color: var(--text);
  padding: 9px 0;
  font-size: 14px;
  outline: none;
  min-width: 160px;
}

.list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.entry {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--card);
  border: 1px solid #2a2f5e;
  border-radius: 14px;
  padding: 14px 18px;
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease;
}
.entry:hover {
  transform: translateY(-2px);
  border-color: var(--accent);
}
.ic {
  color: var(--accent);
  flex: 0 0 auto;
}
.entry.file .ic {
  color: var(--accent-2);
}
.name {
  font-size: 15px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.size {
  margin-left: auto;
  color: var(--text-dim);
  font-size: 13px;
  flex: 0 0 auto;
}

.hint {
  color: var(--text-dim);
  font-size: 15px;
}
.hint.err {
  color: #ff8a8a;
}
</style>

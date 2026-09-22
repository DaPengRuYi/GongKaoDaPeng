<script setup>
import { ref, onMounted } from 'vue'
import { Search, ChevronDown, Calendar } from 'lucide-vue-next'
import { fetchPapers } from '../api/papers.js'

const subject = ref('')
const moduleName = ref('')
const year = ref('')
const q = ref('')
const page = ref(1)
const pageSize = 20

const items = ref([])
const total = ref(0)
const filters = ref({ subjects: [], modules: [], years: [] })
const loading = ref(false)
const error = ref('')
const expandedId = ref(null)

/** 拉取真题列表与筛选项。 */
async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchPapers({
      subject: subject.value,
      module: moduleName.value,
      year: year.value,
      q: q.value,
      page: page.value,
      page_size: pageSize
    })
    items.value = data.items || []
    total.value = data.total || 0
    if (data.filters) filters.value = data.filters
    expandedId.value = null
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

/** 变更筛选条件后回到第一页重新查询。 */
function applyFilters() {
  page.value = 1
  load()
}

function prevPage() {
  if (page.value > 1) {
    page.value--
    load()
  }
}
function nextPage() {
  if (page.value * pageSize < total.value) {
    page.value++
    load()
  }
}

function toggle(id) {
  expandedId.value = expandedId.value === id ? null : id
}

onMounted(load)
</script>

<template>
  <div class="page">
    <h1 class="title">历年真题</h1>

    <div class="filters">
      <select v-model="subject" class="sel" @change="applyFilters">
        <option value="">全部科目</option>
        <option v-for="s in filters.subjects" :key="s" :value="s">{{ s }}</option>
      </select>
      <select v-model="moduleName" class="sel" @change="applyFilters">
        <option value="">全部模块</option>
        <option v-for="m in filters.modules" :key="m" :value="m">{{ m }}</option>
      </select>
      <select v-model="year" class="sel" @change="applyFilters">
        <option value="">全部年份</option>
        <option v-for="y in filters.years" :key="y" :value="y">{{ y }}</option>
      </select>
      <div class="search">
        <Search :size="16" />
        <input v-model="q" class="inp" placeholder="搜索关键字" @keyup.enter="applyFilters" />
      </div>
      <button class="btn ghost" @click="applyFilters">查询</button>
    </div>

    <p v-if="error" class="hint err">{{ error }}</p>
    <p v-if="loading" class="hint">加载中…</p>
    <p v-else-if="!items.length" class="hint">没有匹配的真题</p>

    <ul v-else class="list">
      <li
        v-for="p in items"
        :key="p.id"
        class="pcard"
        :class="{ open: expandedId === p.id }"
      >
        <div class="row" @click="toggle(p.id)">
          <div class="meta">
            <span class="tag">{{ p.subject }}</span>
            <span class="tag dim">{{ p.module }}</span>
            <span v-if="p.is_real" class="tag real">真题</span>
            <span v-if="p.year" class="tag year">
              <Calendar :size="12" /> {{ p.year }}
            </span>
          </div>
          <p class="content">{{ p.content }}</p>
          <div class="right">
            <span class="src">{{ p.source }}</span>
            <ChevronDown :size="18" class="chev" :class="{ up: expandedId === p.id }" />
          </div>
        </div>
        <div v-if="expandedId === p.id" class="detail">
          <div class="options">
            <div v-for="[letter, text] in Object.entries(p.options)" :key="letter" class="opt">
              <span class="letter">{{ letter }}</span>
              <span class="optext">{{ text }}</span>
            </div>
          </div>
        </div>
      </li>
    </ul>

    <div v-if="items.length" class="pager">
      <button class="btn ghost" :disabled="page <= 1" @click="prevPage">上一页</button>
      <span class="pginfo">
        第 {{ page }} 页 / 共 {{ Math.ceil(total / pageSize) || 1 }} 页（{{ total }} 条）
      </span>
      <button class="btn ghost" :disabled="page * pageSize >= total" @click="nextPage">下一页</button>
    </div>
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

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.sel {
  background: var(--bg-soft);
  border: 1px solid #2a2f5e;
  color: var(--text);
  border-radius: 10px;
  padding: 9px 12px;
  font-size: 14px;
  outline: none;
  cursor: pointer;
}
.sel:focus {
  border-color: var(--accent);
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
  min-width: 150px;
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  border-radius: 10px;
  padding: 9px 16px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.15s ease, opacity 0.15s ease;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn.ghost {
  color: var(--text);
  background: var(--bg-soft);
  border: 1px solid #2a2f5e;
}
.btn.ghost:not(:disabled):hover {
  border-color: var(--accent);
}

.list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.pcard {
  background: var(--card);
  border: 1px solid #2a2f5e;
  border-radius: 16px;
  overflow: hidden;
  transition: border-color 0.15s ease;
}
.pcard.open {
  border-color: var(--accent);
}
.row {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-areas: 'meta right' 'content right';
  gap: 6px 16px;
  padding: 16px 18px;
  cursor: pointer;
}
.meta {
  grid-area: meta;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(108, 140, 255, 0.16);
  color: var(--accent);
}
.tag.dim {
  background: rgba(154, 163, 199, 0.14);
  color: var(--text-dim);
}
.tag.real {
  background: rgba(75, 225, 192, 0.16);
  color: var(--accent-2);
}
.tag.year {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.content {
  grid-area: content;
  font-size: 15px;
  line-height: 1.6;
  color: var(--text);
}
.right {
  grid-area: right;
  display: flex;
  align-items: center;
  gap: 12px;
}
.src {
  color: var(--text-dim);
  font-size: 13px;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.chev {
  color: var(--text-dim);
  transition: transform 0.18s ease;
}
.chev.up {
  transform: rotate(180deg);
}

.detail {
  border-top: 1px solid #232850;
  padding: 14px 18px;
  background: rgba(15, 18, 38, 0.4);
}
.options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}
.opt {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-soft);
  border: 1px solid #2a2f5e;
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--text);
}
.letter {
  flex: 0 0 22px;
  height: 22px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(154, 163, 199, 0.18);
  font-weight: 700;
  font-size: 13px;
}
.optext {
  line-height: 1.5;
}

.pager {
  margin-top: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
}
.pginfo {
  color: var(--text-dim);
  font-size: 14px;
}

.hint {
  color: var(--text-dim);
  font-size: 15px;
}
.hint.err {
  color: #ff8a8a;
}

@media (max-width: 720px) {
  .options {
    grid-template-columns: 1fr;
  }
  .src {
    display: none;
  }
}
</style>

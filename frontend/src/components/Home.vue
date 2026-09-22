<script setup>
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import * as Lucide from 'lucide-vue-next'
import { fetchHome } from '../api/home.js'

const data = ref(null)
const loading = ref(true)
const error = ref('')

// 后端只返回图标 name 字符串，前端按 Lucide 注册表动态渲染组件；
// 未知 name 兜底到 BookOpen，保证永不出现空白图标。
function iconFor(name) {
  return Lucide[name] || Lucide.BookOpen
}

// 功能卡 → 路由映射（后端未返回 to 字段时的兜底；
// 若后端 features 含 to 字段则优先使用，见 routeFor）。
const featureRoutes = {
  Brain: '/quiz',
  Target: '/quiz',
  Mic: '/quiz',
  Network: '/materials'
}
function routeFor(f) {
  if (f.to) return f.to
  return featureRoutes[f.icon] || '/'
}

onMounted(async () => {
  try {
    data.value = await fetchHome()
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page">
    <main>
      <section class="hero">
        <p v-if="loading" class="hint">加载中…</p>
        <p v-else-if="error" class="hint err">{{ error }}</p>
        <template v-else-if="data">
          <h1 class="title">{{ data.title }}</h1>
          <p class="subtitle">{{ data.subtitle }}</p>
          <p class="slogan">{{ data.slogan }}</p>
          <a class="cta" :href="data.cta_url">{{ data.cta_text }} →</a>
        </template>
      </section>

      <section class="features" v-if="data && data.features">
        <RouterLink
          v-for="f in data.features"
          :key="f.title"
          :to="routeFor(f)"
          class="card"
        >
          <div class="icon"><component :is="iconFor(f.icon)" :size="34" /></div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </RouterLink>
      </section>
    </main>
  </div>
</template>

<style scoped>
.page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px 48px;
}

.hero {
  padding: 72px 0 56px;
  text-align: center;
}
.title {
  font-size: 56px;
  font-weight: 800;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  letter-spacing: 2px;
}
.subtitle {
  margin-top: 18px;
  font-size: 22px;
  font-weight: 600;
  color: var(--text);
}
.slogan {
  margin-top: 14px;
  font-size: 16px;
  color: var(--text-dim);
  max-width: 640px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.7;
}
.cta {
  display: inline-block;
  margin-top: 32px;
  padding: 14px 34px;
  border-radius: 999px;
  font-size: 16px;
  font-weight: 700;
  color: #0f1226;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  box-shadow: 0 10px 30px rgba(108, 140, 255, 0.35);
  transition: transform 0.15s ease;
}
.cta:hover {
  transform: translateY(-2px);
}

.features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18px;
  margin-top: 18px;
}
.card {
  display: block;
  color: inherit;
  background: var(--card);
  border: 1px solid #2a2f5e;
  border-radius: 18px;
  padding: 26px;
  transition: transform 0.15s ease, border-color 0.15s ease;
}
.card:hover {
  transform: translateY(-3px);
  border-color: var(--accent);
}
.icon {
  color: var(--accent);
  display: flex;
}
.card h3 {
  margin: 12px 0 8px;
  font-size: 18px;
}
.card p {
  color: var(--text-dim);
  font-size: 14px;
  line-height: 1.7;
}

.hint {
  color: var(--text-dim);
  font-size: 16px;
}
.hint.err {
  color: #ff8a8a;
}

@media (max-width: 720px) {
  .features {
    grid-template-columns: 1fr;
  }
  .title {
    font-size: 40px;
  }
}
</style>

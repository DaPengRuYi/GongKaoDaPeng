<script setup>
import { ref, onMounted } from 'vue'
import { fetchHome } from '../api/home.js'

const data = ref(null)
const loading = ref(true)
const error = ref('')

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
    <header class="nav">
      <div class="brand">🦅 公考大鹏</div>
      <nav class="links">
        <a href="#features">能力</a>
        <a href="#cta">开始</a>
        <span class="ver" v-if="data">v{{ data.version }}</span>
      </nav>
    </header>

    <main>
      <section class="hero">
        <p v-if="loading" class="hint">加载中…</p>
        <p v-else-if="error" class="hint err">{{ error }}</p>
        <template v-else-if="data">
          <h1 class="title">{{ data.title }}</h1>
          <p class="subtitle">{{ data.subtitle }}</p>
          <p class="slogan">{{ data.slogan }}</p>
          <a class="cta" :href="data.cta_url" id="cta">{{ data.cta_text }} →</a>
        </template>
      </section>

      <section class="features" id="features" v-if="data && data.features">
        <article
          v-for="f in data.features"
          :key="f.title"
          class="card"
        >
          <div class="icon">{{ f.icon }}</div>
          <h3>{{ f.title }}</h3>
          <p>{{ f.desc }}</p>
        </article>
      </section>
    </main>

    <footer class="foot">
      <span>公考大鹏 · 程序员公考提效平台</span>
      <span>FastAPI + Vue + SQLModel</span>
    </footer>
  </div>
</template>

<style scoped>
.page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px 48px;
}

.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 0;
}
.brand {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 1px;
}
.links {
  display: flex;
  gap: 18px;
  align-items: center;
  color: var(--text-dim);
  font-size: 14px;
}
.links a:hover {
  color: var(--accent);
}
.ver {
  border: 1px solid #2c3260;
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
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
  font-size: 34px;
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

.foot {
  margin-top: 56px;
  padding-top: 22px;
  border-top: 1px solid #232850;
  display: flex;
  justify-content: space-between;
  color: var(--text-dim);
  font-size: 13px;
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

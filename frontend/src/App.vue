<script setup>
import { Bird, Home as HomeIcon, ListChecks, BookOpen, FolderOpen } from 'lucide-vue-next'
import { RouterLink, RouterView } from 'vue-router'

// 顶部导航：图标 + 文案 + 目标路由。
// 图标取自 Lucide 注册表：首页 Home、在线刷题 ListChecks、
// 历年真题 BookOpen、学习资料 FolderOpen，品牌图标 Bird。
const navItems = [
  { to: '/', label: '首页', icon: HomeIcon },
  { to: '/quiz', label: '在线刷题', icon: ListChecks },
  { to: '/papers', label: '历年真题', icon: BookOpen },
  { to: '/materials', label: '学习资料', icon: FolderOpen }
]
</script>

<template>
  <div class="app">
    <header class="topbar">
      <div class="topbar-inner">
        <RouterLink to="/" class="brand" aria-label="公考大鹏首页">
          <Bird :size="22" />
          <span>公考大鹏</span>
        </RouterLink>
        <nav class="nav">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="nav-link"
            active-class="active"
          >
            <component :is="item.icon" :size="18" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </nav>
      </div>
    </header>

    <main class="main">
      <RouterView />
    </main>

    <footer class="foot">
      <span>公考大鹏 · 程序员公考提效平台</span>
      <span>FastAPI + Vue + SQLModel</span>
    </footer>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(15, 18, 38, 0.82);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #232850;
}
.topbar-inner {
  max-width: 1080px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--text);
}
.brand:hover {
  color: var(--accent);
}
.nav {
  display: flex;
  gap: 6px;
  align-items: center;
}
.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 999px;
  color: var(--text-dim);
  font-size: 14px;
  transition: color 0.15s ease, background 0.15s ease;
}
.nav-link:hover {
  color: var(--text);
  background: var(--bg-soft);
}
.nav-link.active {
  color: #0f1226;
  font-weight: 600;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  box-shadow: 0 6px 18px rgba(108, 140, 255, 0.3);
}

.main {
  flex: 1;
}

.foot {
  max-width: 1080px;
  margin: 56px auto 0;
  padding: 22px 24px;
  border-top: 1px solid #232850;
  display: flex;
  justify-content: space-between;
  color: var(--text-dim);
  font-size: 13px;
}

@media (max-width: 720px) {
  .topbar-inner {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  .nav {
    flex-wrap: wrap;
  }
  .foot {
    flex-direction: column;
    gap: 6px;
  }
}
</style>

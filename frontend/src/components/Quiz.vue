<script setup>
import { ref, onMounted, computed } from 'vue'
import { RefreshCw, CheckCircle2, XCircle, BookAlert } from 'lucide-vue-next'
import { fetchRandom, submitAnswer, fetchWrong } from '../api/quiz.js'

const subject = ref('')
const moduleName = ref('')
const questions = ref([])
const answers = ref({}) // { [id]: 'A' | 'B' | 'C' | 'D' }
const results = ref({}) // { [id]: submitResponse }
const loading = ref(false)
const error = ref('')
const quizStart = ref(0)
const gradedAvailable = ref(true)

const showWrongBook = ref(false)
const wrongItems = ref([])
const wrongLoading = ref(false)

/**
 * 抽取一套新题（默认 10 道），可选科目 / 模块筛选。
 */
async function loadQuiz() {
  loading.value = true
  error.value = ''
  results.value = {}
  answers.value = {}
  showWrongBook.value = false
  wrongItems.value = []
  try {
    const data = await fetchRandom({ subject: subject.value, module: moduleName.value, n: 10 })
    questions.value = data.items || []
    gradedAvailable.value = data.graded_available !== false
    quizStart.value = Date.now()
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

/** 选择某题选项（已提交则不可改）。 */
function choose(q, letter) {
  if (results.value[q.id]) return
  answers.value[q.id] = letter
}

/** 提交单题，调用后端判分接口。 */
async function submitOne(q) {
  const chosen = answers.value[q.id]
  if (!chosen || results.value[q.id]) return
  try {
    const res = await submitAnswer({
      question_id: q.id,
      chosen,
      user_id: null,
      time_sec: Math.max(1, Math.floor((Date.now() - quizStart.value) / 1000))
    })
    results.value[q.id] = res
  } catch (e) {
    error.value = e.message || '提交失败'
  }
}

/** 本次得分：已判分题目中答对的数量 / 已判分数量。 */
const score = computed(() => {
  let correct = 0
  let graded = 0
  for (const q of questions.value) {
    const r = results.value[q.id]
    if (r && r.graded) {
      graded++
      if (r.is_correct) correct++
    }
  }
  return { correct, graded }
})

const allSubmitted = computed(
  () => questions.value.length > 0 && questions.value.every((q) => results.value[q.id])
)

/** 选项按钮样式：选中 / 正确(绿) / 错误(红)。 */
function optClass(q, letter) {
  const r = results.value[q.id]
  const selected = answers.value[q.id] === letter
  const cls = { selected }
  if (r && r.graded) {
    if (letter === r.correct) cls.correct = true
    if (selected && !r.is_correct) cls.wrong = true
  }
  return cls
}

/** 单题结果类型：ok(对) / bad(错) / neutral(无标准答案)。 */
function resultType(q) {
  const r = results.value[q.id]
  if (!r) return ''
  if (!r.graded) return 'neutral'
  return r.is_correct ? 'ok' : 'bad'
}

/** 拉取错题本。 */
async function openWrongBook() {
  wrongLoading.value = true
  error.value = ''
  try {
    const data = await fetchWrong({ limit: 50 })
    wrongItems.value = data.items || []
    showWrongBook.value = true
  } catch (e) {
    error.value = e.message || '加载错题本失败'
  } finally {
    wrongLoading.value = false
  }
}

onMounted(loadQuiz)
</script>

<template>
  <div class="page">
    <div class="head">
      <h1 class="title">在线刷题</h1>
      <div class="filters">
        <input v-model="subject" class="inp" placeholder="科目（可选）" />
        <input v-model="moduleName" class="inp" placeholder="模块（可选）" />
        <button class="btn ghost" :disabled="loading" @click="loadQuiz">
          <RefreshCw :size="16" /> 重抽一套
        </button>
      </div>
    </div>

    <p v-if="error" class="hint err">{{ error }}</p>
    <p v-if="loading" class="hint">加载中…</p>
    <p v-if="!loading && !gradedAvailable" class="hint dim">
      本套题暂无标准答案，提交后将提示「暂无标准答案，请自行核对」。
    </p>

    <section v-if="!loading && questions.length" class="list">
      <article v-for="(q, idx) in questions" :key="q.id" class="qcard">
        <div class="qmeta">
          <span class="tag">{{ q.subject }}</span>
          <span class="tag dim">{{ q.module }}</span>
          <span class="qno">#{{ idx + 1 }}</span>
        </div>
        <p class="qcontent">{{ q.content }}</p>

        <div class="options">
          <button
            v-for="[letter, text] in Object.entries(q.options)"
            :key="letter"
            class="opt"
            :class="optClass(q, letter)"
            :disabled="!!results[q.id]"
            @click="choose(q, letter)"
          >
            <span class="letter">{{ letter }}</span>
            <span class="optext">{{ text }}</span>
          </button>
        </div>

        <div class="actions">
          <button
            v-if="!results[q.id]"
            class="btn primary"
            :disabled="!answers[q.id]"
            @click="submitOne(q)"
          >
            提交本题
          </button>

          <div v-else class="result" :class="resultType(q)">
            <component
              :is="results[q.id].graded ? (results[q.id].is_correct ? CheckCircle2 : XCircle) : BookAlert"
              :size="18"
            />
            <span v-if="!results[q.id].graded">暂无标准答案，请自行核对</span>
            <span v-else-if="results[q.id].is_correct">回答正确</span>
            <span v-else>回答错误，正确答案：{{ results[q.id].correct }}</span>
          </div>
        </div>

        <p v-if="results[q.id] && results[q.id].analysis" class="analysis">
          <strong>解析：</strong>{{ results[q.id].analysis }}
        </p>
      </article>
    </section>

    <section v-if="allSubmitted" class="summary">
      <div class="score">
        本次得分：<b>{{ score.correct }}</b> / {{ score.graded }}
        <span v-if="score.graded < questions.length" class="muted">
          （{{ questions.length - score.graded }} 题无标准答案，未计入）
        </span>
      </div>
      <button class="btn ghost" :disabled="wrongLoading" @click="openWrongBook">
        <BookAlert :size="16" /> 查看错题本
      </button>
    </section>

    <section v-if="showWrongBook" class="wrongbook">
      <h2>错题本</h2>
      <p v-if="wrongLoading" class="hint">加载中…</p>
      <p v-else-if="!wrongItems.length" class="hint">暂无错题记录</p>
      <ul v-else class="wb-list">
        <li v-for="w in wrongItems" :key="w.id" class="wb-item">
          <div class="qmeta">
            <span class="tag">{{ w.subject }}</span>
            <span class="tag dim">{{ w.module }}</span>
          </div>
          <p class="qcontent">{{ w.content }}</p>
          <p class="wb-ans">你的答案：{{ w.chosen }} ｜ 正确答案：{{ w.correct }}</p>
          <p v-if="w.analysis" class="analysis"><strong>解析：</strong>{{ w.analysis }}</p>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.page {
  max-width: 880px;
  margin: 0 auto;
  padding: 40px 24px 24px;
}

.head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 22px;
}
.title {
  font-size: 30px;
  font-weight: 800;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.filters {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.inp {
  background: var(--bg-soft);
  border: 1px solid #2a2f5e;
  color: var(--text);
  border-radius: 10px;
  padding: 9px 12px;
  font-size: 14px;
  outline: none;
  min-width: 130px;
}
.inp:focus {
  border-color: var(--accent);
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
.btn.primary {
  color: #0f1226;
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
}
.btn.primary:not(:disabled):hover {
  transform: translateY(-1px);
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
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.qcard {
  background: var(--card);
  border: 1px solid #2a2f5e;
  border-radius: 18px;
  padding: 22px 24px;
}
.qmeta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
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
.qno {
  margin-left: auto;
  color: var(--text-dim);
  font-size: 13px;
}
.qcontent {
  font-size: 16px;
  line-height: 1.7;
  margin-bottom: 14px;
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
  text-align: left;
  background: var(--bg-soft);
  border: 1px solid #2a2f5e;
  color: var(--text);
  border-radius: 12px;
  padding: 12px 14px;
  font-size: 14px;
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}
.opt:not(:disabled):hover {
  border-color: var(--accent);
}
.opt.selected {
  border-color: var(--accent);
  background: rgba(108, 140, 255, 0.14);
}
.opt.correct {
  border-color: #3ddc84;
  background: rgba(61, 220, 132, 0.14);
  color: #b9f5cf;
}
.opt.wrong {
  border-color: #ff6b6b;
  background: rgba(255, 107, 107, 0.14);
  color: #ffc2c2;
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

.actions {
  margin-top: 16px;
}
.result {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}
.result.ok {
  color: #3ddc84;
}
.result.bad {
  color: #ff6b6b;
}
.result.neutral {
  color: var(--text-dim);
}

.analysis {
  margin-top: 12px;
  font-size: 14px;
  color: var(--text-dim);
  line-height: 1.7;
  background: rgba(154, 163, 199, 0.08);
  border-radius: 10px;
  padding: 10px 14px;
}

.summary {
  margin-top: 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  background: var(--card);
  border: 1px solid #2a2f5e;
  border-radius: 18px;
  padding: 20px 24px;
}
.score {
  font-size: 16px;
  color: var(--text);
}
.score b {
  font-size: 24px;
  color: var(--accent-2);
}
.muted {
  color: var(--text-dim);
  font-size: 13px;
}

.wrongbook {
  margin-top: 22px;
}
.wrongbook h2 {
  font-size: 20px;
  margin-bottom: 12px;
}
.wb-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.wb-item {
  background: var(--card);
  border: 1px solid #2a2f5e;
  border-radius: 14px;
  padding: 16px 18px;
}
.wb-ans {
  margin-top: 8px;
  font-size: 14px;
  color: var(--text-dim);
}

.hint {
  color: var(--text-dim);
  font-size: 15px;
}
.hint.err {
  color: #ff8a8a;
}
.hint.dim {
  color: var(--text-dim);
}

@media (max-width: 720px) {
  .options {
    grid-template-columns: 1fr;
  }
}
</style>

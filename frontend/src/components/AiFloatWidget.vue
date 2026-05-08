<script setup lang="ts">
import { ref, reactive, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { marked } from 'marked'
import {
  policyQaStreamApi,
  generateCertificateTextStreamApi,
  getRecommendApi,
  type RecommendItem,
} from '@/api/ai'
import { ElMessage } from 'element-plus'
import { PROJECT_CATEGORIES } from '@/constants/category'

const router = useRouter()
const userStore = useUserStore()
const open = ref(false)

function renderMd(text: string): string {
  if (!text) return ''
  const cleaned = text.replace(/\{data-source-line="[^"]*"\}/g, '').trim()
  if (!cleaned) return ''
  return marked.parse(cleaned, { breaks: true }) as string
}

// ========== 智能问答 ==========
interface ChatMessage { role: 'user' | 'assistant'; content: string }
const chatMessages = ref<ChatMessage[]>([])
const chatInput = ref('')
const chatLoading = ref(false)
const chatAreaRef = ref<HTMLElement>()

async function handleSendQuestion() {
  const question = chatInput.value.trim()
  if (!question || chatLoading.value) return
  chatMessages.value.push({ role: 'user', content: question })
  chatInput.value = ''
  chatLoading.value = true
  const aiMsg: ChatMessage = { role: 'assistant', content: '' }
  chatMessages.value.push(aiMsg)
  await nextTick(); scrollToBottom()
  await policyQaStreamApi(
    question,
    (chunk) => { aiMsg.content += chunk; chatMessages.value = [...chatMessages.value]; nextTick(scrollToBottom) },
    () => { chatLoading.value = false; if (!aiMsg.content) { aiMsg.content = '未获取到回答，请稍后重试。'; chatMessages.value = [...chatMessages.value] } },
    (err) => { aiMsg.content = `请求失败：${err}`; chatMessages.value = [...chatMessages.value]; chatLoading.value = false },
  )
}
function scrollToBottom() { if (chatAreaRef.value) chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight }

// ========== 证书文案 ==========
const certForm = reactive({ userName: '', projectTitle: '', durationHours: 0, category: '' })
const certResult = ref('')
const certLoading = ref(false)

async function handleGenerateText() {
  if (!certForm.userName || !certForm.projectTitle) { ElMessage.warning('请填写姓名和项目名称'); return }
  if (certLoading.value) return
  certLoading.value = true; certResult.value = ''
  await generateCertificateTextStreamApi(
    certForm,
    (chunk) => { certResult.value += chunk },
    () => { certLoading.value = false; if (!certResult.value) certResult.value = '未生成文案，请稍后重试。' },
    (err) => { certResult.value = `生成失败：${err}`; certLoading.value = false },
  )
}
function handleCopyText() {
  if (!certResult.value) return
  navigator.clipboard.writeText(certResult.value).then(() => ElMessage.success('已复制到剪贴板')).catch(() => ElMessage.error('复制失败'))
}

// ========== 项目推荐 ==========
const recLoading = ref(false)
const recList = ref<RecommendItem[]>([])
async function fetchRecommend() {
  recLoading.value = true
  try { const res = await getRecommendApi(); recList.value = res.data } catch { ElMessage.error('获取推荐失败') } finally { recLoading.value = false }
}
function goProject(id: number) { router.push(`/project/${id}`) }
function formatTime(t: string | null) { return t ? t.replace('T', ' ').slice(0, 10) : '--' }
</script>

<template>
  <!-- 悬浮按钮 -->
  <div
    v-if="!open"
    class="fixed bottom-6 right-6 z-[1000] w-14 h-14 rounded-full bg-gradient-to-br from-[#4F6EF7] to-[#6C8CFA] hover:from-[#3F58C6] hover:to-[#5A7AF0] text-white flex items-center justify-center cursor-pointer shadow-lg transition-all hover:scale-110"
    @click="open = true"
  >
    <el-icon size="28"><ChatDotRound /></el-icon>
  </div>

  <!-- 悬浮面板 -->
  <transition name="ai-panel">
    <div v-if="open" class="fixed z-[1000] bg-white flex flex-col overflow-hidden ai-float-panel">
      <!-- 头部 -->
      <div class="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-[#4F6EF7] to-[#6C8CFA] text-white flex-shrink-0">
        <div class="flex items-center gap-2">
          <el-icon size="20"><ChatDotRound /></el-icon>
          <span class="font-semibold text-sm">AI 智能助手</span>
        </div>
        <div class="cursor-pointer hover:bg-white/20 rounded p-1 transition" @click="open = false">
          <el-icon size="18"><Close /></el-icon>
        </div>
      </div>

      <!-- 内容 -->
      <div class="flex-1 overflow-hidden">
        <el-tabs type="card" class="ai-float-tabs h-full flex flex-col">
          <!-- 智能问答 -->
          <el-tab-pane label="智能问答">
            <div class="flex flex-col h-[460px]">
              <div ref="chatAreaRef" class="flex-1 overflow-y-auto p-3 space-y-2">
                <div v-if="chatMessages.length === 0" class="text-center text-gray-400 mt-16 text-sm">
                  <el-icon size="36"><ChatDotRound /></el-icon>
                  <p class="mt-2">输入问题，AI为您解答</p>
                </div>
                <div v-for="(msg, idx) in chatMessages" :key="idx" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
                  <div class="max-w-[80%] px-3 py-2 rounded-lg text-xs leading-relaxed" :class="msg.role === 'user' ? 'bg-blue-500 text-white rounded-br-none' : 'bg-gray-100 text-gray-700 rounded-bl-none'">
                    <template v-if="msg.role === 'user'">{{ msg.content }}</template>
                    <div v-else v-html="renderMd(msg.content)" class="markdown-body" />
                    <span v-if="msg.role === 'assistant' && chatLoading && idx === chatMessages.length - 1 && msg.content" class="inline-block w-1 h-3 bg-gray-400 ml-0.5 animate-pulse align-middle" />
                  </div>
                </div>
                <div v-if="chatLoading && chatMessages.length > 0 && !chatMessages[chatMessages.length - 1].content" class="flex justify-start">
                  <div class="bg-gray-100 px-3 py-2 rounded-lg rounded-bl-none text-xs text-gray-400">AI 正在思考...</div>
                </div>
              </div>
              <div class="flex gap-2 p-3 border-t border-gray-100 flex-shrink-0">
                <el-input v-model="chatInput" size="small" placeholder="请输入问题..." :disabled="chatLoading" @keyup.enter="handleSendQuestion" />
                <el-button type="primary" size="small" :loading="chatLoading" @click="handleSendQuestion">发送</el-button>
              </div>
            </div>
          </el-tab-pane>

          <!-- 证书文案 -->
          <el-tab-pane label="证书文案">
            <div class="p-3 overflow-y-auto h-[460px]">
              <el-form :model="certForm" label-width="80px" size="small">
                <el-form-item label="姓名"><el-input v-model="certForm.userName" placeholder="志愿者姓名" /></el-form-item>
                <el-form-item label="项目"><el-input v-model="certForm.projectTitle" placeholder="项目名称" /></el-form-item>
                <el-form-item label="时长">
                  <el-input-number v-model="certForm.durationHours" :min="0" :precision="2" size="small" />
                  <span class="ml-1 text-gray-400 text-xs">小时</span>
                </el-form-item>
                <el-form-item label="类型">
                  <el-select v-model="certForm.category" placeholder="选择类型" size="small">
                    <el-option v-for="c in PROJECT_CATEGORIES" :key="c" :label="c" :value="c" />
                  </el-select>
                </el-form-item>
                <el-form-item><el-button type="primary" size="small" :loading="certLoading" @click="handleGenerateText">生成文案</el-button></el-form-item>
              </el-form>
              <div v-if="certResult || certLoading" class="mt-2">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-xs font-semibold text-gray-600">生成结果 <span v-if="certLoading" class="text-gray-400 font-normal">生成中...</span></span>
                  <el-button v-if="certResult && !certLoading" type="primary" text size="small" @click="handleCopyText">复制</el-button>
                </div>
                <el-input v-model="certResult" type="textarea" :rows="5" :readonly="certLoading" size="small" />
              </div>
            </div>
          </el-tab-pane>

          <!-- 项目推荐（仅学生） -->
          <el-tab-pane v-if="userStore.role === 'student'" label="项目推荐">
            <div class="p-3 overflow-y-auto h-[460px]">
              <div class="flex items-center justify-between mb-3">
                <span class="text-xs text-gray-500">根据您的偏好推荐</span>
                <el-button type="primary" size="small" :loading="recLoading" @click="fetchRecommend"><el-icon><Refresh /></el-icon> 刷新</el-button>
              </div>
              <div v-loading="recLoading" class="space-y-3">
                <div v-for="item in recList" :key="item.projectId" class="border border-gray-200 rounded-lg p-3 cursor-pointer hover:shadow-md transition" @click="goProject(item.projectId)">
                  <div class="flex items-center justify-between mb-1">
                    <span class="font-semibold text-sm text-gray-800">{{ item.title }}</span>
                    <el-tag size="small" type="info">{{ item.category || '其他' }}</el-tag>
                  </div>
                  <div class="text-xs text-gray-400 space-y-0.5">
                    <div v-if="item.location"><el-icon size="12"><Location /></el-icon> {{ item.location }}</div>
                    <div><el-icon size="12"><Calendar /></el-icon> {{ formatTime(item.startTime) }} ~ {{ formatTime(item.endTime) }}</div>
                  </div>
                  <div v-if="item.reason" class="text-xs text-blue-600 bg-blue-50 rounded px-2 py-1 mt-2">
                    <el-icon size="12"><MagicStick /></el-icon> {{ item.reason }}
                  </div>
                </div>
                <el-empty v-if="!recLoading && recList.length === 0" description="暂无推荐" :image-size="60" />
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.ai-panel-enter-active, .ai-panel-leave-active {
  transition: all 0.3s ease;
}
.ai-panel-enter-from, .ai-panel-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
/* 桌面端面板 */
.ai-float-panel {
  bottom: 24px;
  right: 24px;
  width: 420px;
  height: 580px;
  border-radius: 16px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  border: 1px solid #e5e7eb;
}
/* 移动端面板全屏 */
@media (max-width: 640px) {
  .ai-float-panel {
    top: 0; left: 0; right: 0; bottom: 0;
    width: 100%; height: 100%;
    border-radius: 0;
    border: none;
  }
}
.ai-float-tabs :deep(.el-tabs__header) {
  margin: 0;
}
.ai-float-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}
.ai-float-tabs :deep(.el-tab-pane) {
  height: 100%;
}
.markdown-body :deep(p) {
  margin: 0.3em 0;
}
</style>

import request from './request'

// 智能政策问答（阻塞模式）
export function policyQaApi(question: string) {
  return request.post('/ai/policy-qa', { question })
}

// 证书文案生成（阻塞模式）
export interface CertificateTextParams {
  userName: string
  projectTitle: string
  durationHours: number
  category?: string
}

export function generateCertificateTextApi(data: CertificateTextParams) {
  return request.post('/ai/certificate-text', data)
}

// ========== 流式调用 ==========

/**
 * 通用 SSE 流式请求底层实现（policy-qa / certificate-text / nl-query 共用）
 *
 * 用原生 fetch 调用后端流式端点，按 \n\n 拆 SSE 事件，每个 `data:` 行解析成 JSON 对象后
 * 整个对象交给 onEvent 回调。上层包装函数自行决定关心哪些字段（content / chart / status）。
 */
async function streamSSE(
  url: string,
  body: Record<string, unknown>,
  onEvent: (obj: Record<string, unknown>) => void,
  onDone?: () => void,
  onError?: (err: string) => void,
) {
  const token = localStorage.getItem('token')
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'

  let resp: Response
  try {
    resp = await fetch(`${baseUrl}${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    })
  } catch (e) {
    onError?.(`无法连接服务器：${(e as Error).message}`)
    onDone?.()
    return
  }

  if (!resp.ok || !resp.body) {
    onError?.(`请求失败 (${resp.status})`)
    onDone?.()
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    // 按双换行拆分 SSE 事件
    const parts = buffer.split('\n\n')
    // 最后一段可能不完整，留在 buffer 等下一轮
    buffer = parts.pop() || ''

    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data:')) continue
      const dataStr = line.slice(5).trim()
      if (dataStr === '[DONE]') {
        onDone?.()
        return
      }
      try {
        onEvent(JSON.parse(dataStr))
      } catch {
        // 忽略不规范的 SSE 数据帧
      }
    }
  }

  onDone?.()
}

// 智能政策问答（流式）
export function policyQaStreamApi(
  question: string,
  onChunk: (text: string) => void,
  onDone?: () => void,
  onError?: (err: string) => void,
) {
  return streamSSE(
    '/ai/policy-qa/stream',
    { question },
    (obj) => { if (obj.content) onChunk(obj.content as string) },
    onDone,
    onError,
  )
}

// 证书文案生成（流式）
export function generateCertificateTextStreamApi(
  params: CertificateTextParams,
  onChunk: (text: string) => void,
  onDone?: () => void,
  onError?: (err: string) => void,
) {
  return streamSSE(
    '/ai/certificate-text/stream',
    { ...params },
    (obj) => { if (obj.content) onChunk(obj.content as string) },
    onDone,
    onError,
  )
}

// ========== 自然语言数据查询（生成式UI） ==========

export interface ChartData {
  type: 'bar' | 'pie' | 'line'
  title: string
  xAxis?: string[]
  series?: Array<{ name: string; data: Array<number | { name: string; value: number }> }>
  labels?: string[]
  values?: number[]
}

/**
 * 自然语言查询（流式 · 生成式UI）
 * onChunk: 接收AI分析文本块（流式逐字）
 * onChart: 接收单个图表数据（后端解析 ```chart 块后逐个推送）
 * onStatus: 接收状态提示
 */
export function nlQueryStreamApi(
  question: string,
  onChunk: (text: string) => void,
  onChart: (data: ChartData) => void,
  onDone?: () => void,
  onError?: (err: string) => void,
  onStatus?: (msg: string) => void,
) {
  return streamSSE(
    '/ai/nl-query/stream',
    { question },
    (obj) => {
      if (obj.type === 'status' && obj.content) {
        onStatus?.(obj.content as string)
      } else if (obj.type === 'chart' && obj.data) {
        onChart(obj.data as ChartData)
      } else if (obj.content) {
        onChunk(obj.content as string)
      }
    },
    onDone,
    onError,
  )
}

// ========== 项目推荐 ==========

export interface RecommendItem {
  projectId: number
  title: string
  category: string
  location: string
  startTime: string | null
  endTime: string | null
  maxPeople: number
  creatorName: string | null
  reason: string
}

export function getRecommendApi() {
  return request.get('/ai/recommend')
}

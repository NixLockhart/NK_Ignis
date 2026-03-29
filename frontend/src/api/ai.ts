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
 * 通用 SSE 流式请求
 * 用原生 fetch 调用后端流式端点，逐块解析并回调
 */
async function fetchSSE(
  url: string,
  body: Record<string, unknown>,
  onChunk: (text: string) => void,
  onDone?: () => void,
  onError?: (err: string) => void,
) {
  const token = localStorage.getItem('token')
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api'

  const resp = await fetch(`${baseUrl}${url}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })

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
    // 最后一个可能不完整，留在 buffer
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
        const obj = JSON.parse(dataStr)
        if (obj.content) {
          onChunk(obj.content)
        }
      } catch {
        // 忽略解析错误
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
  return fetchSSE('/ai/policy-qa/stream', { question }, onChunk, onDone, onError)
}

// 证书文案生成（流式）
export function generateCertificateTextStreamApi(
  params: CertificateTextParams,
  onChunk: (text: string) => void,
  onDone?: () => void,
  onError?: (err: string) => void,
) {
  return fetchSSE('/ai/certificate-text/stream', params, onChunk, onDone, onError)
}

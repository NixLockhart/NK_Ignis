import json
import requests
from flask import current_app


def policy_qa(question, user_id, role='student'):
    """智能政策问答 — 阻塞模式"""
    base_url = _get_base_url()
    api_key = current_app.config.get('DIFY_QA_API_KEY', '')
    if not base_url or not api_key:
        return {'answer': 'AI服务尚未配置，请联系管理员。'}

    payload = {
        'inputs': {'role': role},
        'query': question,
        'response_mode': 'blocking',
        'conversation_id': '',
        'user': str(user_id),
    }

    try:
        result = _call_dify_api(f'{base_url}/chat-messages', api_key, payload)
        return {'answer': result.get('answer', '未获取到回答，请稍后重试。')}
    except Exception as e:
        return {'answer': f'AI服务调用失败：{str(e)}'}


def policy_qa_stream(question, user_id, role='student'):
    """智能政策问答 — 流式模式，返回生成器"""
    base_url = _get_base_url()
    api_key = current_app.config.get('DIFY_QA_API_KEY', '')
    if not base_url or not api_key:
        yield _sse_data({'content': 'AI服务尚未配置，请联系管理员。'})
        yield _sse_done()
        return

    payload = {
        'inputs': {'role': role},
        'query': question,
        'response_mode': 'streaming',
        'conversation_id': '',
        'user': str(user_id),
    }

    try:
        for chunk in _stream_dify_api(f'{base_url}/chat-messages', api_key, payload, 'chat'):
            yield chunk
    except Exception as e:
        yield _sse_data({'content': f'\n\n[错误: {str(e)}]'})
    finally:
        yield _sse_done()


def generate_certificate_text(user_name, project_title, duration_hours, category=None):
    """证书文案生成 — 阻塞模式"""
    base_url = _get_base_url()
    api_key = current_app.config.get('DIFY_CERT_API_KEY', '')
    if not base_url or not api_key:
        return {'text': 'AI服务尚未配置，请联系管理员。'}

    payload = {
        'inputs': {
            'name': user_name,
            'project': project_title,
            'time': str(duration_hours),
            'category': category or '其他',
        },
        'response_mode': 'blocking',
        'user': 'system',
    }

    try:
        result = _call_dify_api(f'{base_url}/workflows/run', api_key, payload)
        outputs = result.get('data', {}).get('outputs', {})
        text = outputs.get('text') or outputs.get('result') or outputs.get('output') or ''
        if not text:
            for v in outputs.values():
                if isinstance(v, str) and len(v) > 10:
                    text = v
                    break
        return {'text': text or '未生成文案，请稍后重试。'}
    except Exception as e:
        return {'text': f'AI服务调用失败：{str(e)}'}


def generate_certificate_text_stream(user_name, project_title, duration_hours, category=None):
    """证书文案生成 — 流式模式，返回生成器"""
    base_url = _get_base_url()
    api_key = current_app.config.get('DIFY_CERT_API_KEY', '')
    if not base_url or not api_key:
        yield _sse_data({'content': 'AI服务尚未配置，请联系管理员。'})
        yield _sse_done()
        return

    payload = {
        'inputs': {
            'name': user_name,
            'project': project_title,
            'time': str(duration_hours),
            'category': category or '其他',
        },
        'response_mode': 'streaming',
        'user': 'system',
    }

    try:
        for chunk in _stream_dify_api(f'{base_url}/workflows/run', api_key, payload, 'workflow'):
            yield chunk
    except Exception as e:
        yield _sse_data({'content': f'\n\n[错误: {str(e)}]'})
    finally:
        yield _sse_done()



# ========== 内部工具函数 ==========

def _call_dify_api(url, api_key, payload):
    """调用 Dify API（阻塞模式）"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    if resp.status_code != 200:
        try:
            err_msg = resp.json().get('message', resp.text)
        except Exception:
            err_msg = resp.text
        raise RuntimeError(f'Dify返回错误({resp.status_code}): {err_msg}')
    return resp.json()


def _stream_dify_api(url, api_key, payload, mode='chat'):
    """调用 Dify API（流式模式），解析 SSE 并 yield 文本块"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=120, stream=True)
    if resp.status_code != 200:
        try:
            err_msg = resp.json().get('message', resp.text)
        except Exception:
            err_msg = resp.text
        yield _sse_data({'content': f'AI服务调用失败：{err_msg}'})
        return

    llm_done = False  # 标记 LLM 节点是否已完成，防止"直接回复"节点重发内容

    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith('data:'):
            continue

        data_str = line[5:].strip()
        if not data_str:
            continue

        try:
            event = json.loads(data_str)
        except json.JSONDecodeError:
            continue

        event_type = event.get('event', '')

        # Chat 模式
        if mode == 'chat':
            # 检测 LLM 节点完成
            if event_type == 'node_finished':
                node_type = event.get('data', {}).get('node_type', '')
                if node_type == 'llm':
                    llm_done = True

            # 只在 LLM 节点完成前接收 message 事件
            if event_type in ('message', 'agent_message') and not llm_done:
                answer = event.get('answer', '')
                if answer:
                    yield _sse_data({'content': answer})
            elif event_type in ('message_end', 'workflow_finished'):
                break

        # Workflow 模式：text_chunk 事件包含增量文本
        elif mode == 'workflow' and event_type == 'text_chunk':
            text = event.get('data', {}).get('text', '')
            if text:
                yield _sse_data({'content': text})

        elif mode == 'workflow' and event_type == 'workflow_finished':
            break  # 工作流结束，主动退出


def _sse_data(obj):
    """格式化 SSE data 行"""
    return f'data: {json.dumps(obj, ensure_ascii=False)}\n\n'


def _sse_done():
    """SSE 结束标记"""
    return 'data: [DONE]\n\n'


def _get_base_url():
    """获取 Dify 基础 URL"""
    return current_app.config.get('DIFY_BASE_URL', '')

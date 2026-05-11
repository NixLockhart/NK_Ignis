from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import ai_service
from services import recommend_service
from models.user import User
from utils.response import success, error
from utils.log_util import log_operation
from utils.auth import require_current_user
from utils.ratelimit import rate_limit

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


# 各 AI 接口的限流配置（限制周期/秒，限制次数）
# 政策问答可频繁、NL 查询管控更严
_RL_POLICY_QA = (60, 30)        # 1 分钟内 30 次
_RL_CERT_TEXT = (60, 20)        # 1 分钟内 20 次
_RL_NL_QUERY = (60, 10)         # 1 分钟内 10 次
_RL_RECOMMEND = (60, 30)        # 1 分钟内 30 次


def _check_rate(user_id: int, key_prefix: str, conf: tuple):
    """统一的限流校验：返回 (allowed, error_response)"""
    window, limit = conf
    if not rate_limit(f'{key_prefix}:{user_id}', limit=limit, window_sec=window):
        return False, error(f'请求过于频繁，请稍候再试（{window} 秒内最多 {limit} 次）', 429)
    return True, None


@ai_bp.route('/policy-qa', methods=['POST'])
@jwt_required()
def policy_qa():
    """智能政策问答（阻塞模式）"""
    user = require_current_user()
    ok, err_resp = _check_rate(user.id, 'ai_policy_qa', _RL_POLICY_QA)
    if not ok:
        return err_resp

    data = request.get_json() or {}
    if not data.get('question', '').strip():
        return error('请输入问题')

    question = data['question'].strip()
    if len(question) > 500:
        return error('问题长度不能超过500字')

    result = ai_service.policy_qa(question, user.id, user.role)
    log_operation(user.id, 'ai_policy_qa', detail=f'问题：{question[:100]}')
    return success(data=result)


@ai_bp.route('/policy-qa/stream', methods=['POST'])
@jwt_required()
def policy_qa_stream():
    """智能政策问答（流式模式）"""
    user = require_current_user()
    ok, err_resp = _check_rate(user.id, 'ai_policy_qa', _RL_POLICY_QA)
    if not ok:
        return err_resp

    data = request.get_json() or {}
    if not data.get('question', '').strip():
        return error('请输入问题')

    question = data['question'].strip()
    if len(question) > 500:
        return error('问题长度不能超过500字')

    # 先记录日志（流式中无法操作数据库）
    log_operation(user.id, 'ai_policy_qa', detail=f'问题：{question[:100]}')

    generator = ai_service.policy_qa_stream(question, user.id, user.role)
    return Response(
        stream_with_context(generator),
        content_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@ai_bp.route('/certificate-text', methods=['POST'])
@jwt_required()
def certificate_text():
    """证书文案生成（阻塞模式）"""
    user = require_current_user()
    ok, err_resp = _check_rate(user.id, 'ai_certificate_text', _RL_CERT_TEXT)
    if not ok:
        return err_resp

    data = request.get_json() or {}

    user_name = data.get('userName', '').strip()
    project_title = data.get('projectTitle', '').strip()
    duration_hours = data.get('durationHours', 0)

    if not user_name or not project_title:
        return error('姓名和项目名称不能为空')

    result = ai_service.generate_certificate_text(
        user_name=user_name,
        project_title=project_title,
        duration_hours=duration_hours,
        category=data.get('category', ''),
    )
    log_operation(
        user.id, 'ai_certificate_text', 'certificate', None,
        f'为 {user_name} 生成 {project_title} 证书文案',
    )
    return success(data=result)


@ai_bp.route('/certificate-text/stream', methods=['POST'])
@jwt_required()
def certificate_text_stream():
    """证书文案生成（流式模式）"""
    user = require_current_user()
    ok, err_resp = _check_rate(user.id, 'ai_certificate_text', _RL_CERT_TEXT)
    if not ok:
        return err_resp

    data = request.get_json() or {}

    user_name = data.get('userName', '').strip()
    project_title = data.get('projectTitle', '').strip()
    duration_hours = data.get('durationHours', 0)

    if not user_name or not project_title:
        return error('姓名和项目名称不能为空')

    log_operation(
        user.id, 'ai_certificate_text', 'certificate', None,
        f'为 {user_name} 生成 {project_title} 证书文案',
    )

    generator = ai_service.generate_certificate_text_stream(
        user_name=user_name,
        project_title=project_title,
        duration_hours=duration_hours,
        category=data.get('category', ''),
    )
    return Response(
        stream_with_context(generator),
        content_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@ai_bp.route('/nl-query/stream', methods=['POST'])
@jwt_required()
def nl_query_stream():
    """自然语言数据查询（流式：查DB→Dify分析→流式返回分析文本+图表数据）"""
    user = require_current_user()
    if user.role != 'admin':
        return error('数据查询功能仅限管理员使用', 403)

    ok, err_resp = _check_rate(user.id, 'ai_nl_query', _RL_NL_QUERY)
    if not ok:
        return err_resp

    data = request.get_json() or {}
    if not data.get('question', '').strip():
        return error('请输入查询问题')

    question = data['question'].strip()
    log_operation(user.id, 'ai_nl_query', detail=f'查询：{question[:100]}')

    generator = ai_service.nl_query_stream(question, user.id, user.role)
    return Response(
        stream_with_context(generator),
        content_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@ai_bp.route('/recommend', methods=['GET'])
@jwt_required()
def recommend():
    """项目智能推荐（仅学生）"""
    user = require_current_user()
    if user.role != 'student':
        return error('推荐功能仅面向学生', 403)

    ok, err_resp = _check_rate(user.id, 'ai_recommend', _RL_RECOMMEND)
    if not ok:
        return err_resp

    log_operation(user.id, 'ai_recommend', detail='获取项目推荐')

    result = recommend_service.get_recommendations_with_ai(user.id)
    return success(data=result)

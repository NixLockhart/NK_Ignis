from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import ai_service
from services import recommend_service
from models.user import User
from utils.response import success, error
from utils.log_util import log_operation

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


@ai_bp.route('/policy-qa', methods=['POST'])
@jwt_required()
def policy_qa():
    """智能政策问答（阻塞模式）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    data = request.get_json()
    if not data or not data.get('question', '').strip():
        return error('请输入问题')

    question = data['question'].strip()
    if len(question) > 500:
        return error('问题长度不能超过500字')

    result = ai_service.policy_qa(question, user_id, user.role)
    log_operation(user_id, 'ai_policy_qa', detail=f'问题：{question[:100]}')
    return success(data=result)


@ai_bp.route('/policy-qa/stream', methods=['POST'])
@jwt_required()
def policy_qa_stream():
    """智能政策问答（流式模式）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    data = request.get_json()
    if not data or not data.get('question', '').strip():
        return error('请输入问题')

    question = data['question'].strip()
    if len(question) > 500:
        return error('问题长度不能超过500字')

    # 先记录日志（流式中无法操作数据库）
    log_operation(user_id, 'ai_policy_qa', detail=f'问题：{question[:100]}')

    generator = ai_service.policy_qa_stream(question, user_id, user.role)
    return Response(
        stream_with_context(generator),
        content_type='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'},
    )


@ai_bp.route('/certificate-text', methods=['POST'])
@jwt_required()
def certificate_text():
    """证书文案生成（阻塞模式）"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return error('请求数据不能为空')

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
        user_id, 'ai_certificate_text', 'certificate', None,
        f'为 {user_name} 生成 {project_title} 证书文案',
    )
    return success(data=result)


@ai_bp.route('/certificate-text/stream', methods=['POST'])
@jwt_required()
def certificate_text_stream():
    """证书文案生成（流式模式）"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return error('请求数据不能为空')

    user_name = data.get('userName', '').strip()
    project_title = data.get('projectTitle', '').strip()
    duration_hours = data.get('durationHours', 0)

    if not user_name or not project_title:
        return error('姓名和项目名称不能为空')

    log_operation(
        user_id, 'ai_certificate_text', 'certificate', None,
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

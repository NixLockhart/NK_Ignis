from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.project import Project
from services import certificate_service, cert_pdf_service
from utils.response import success, error
from utils.log_util import log_operation
from utils.auth import require_current_user

certificate_bp = Blueprint('certificate', __name__, url_prefix='/api/certificate')


def _get_current_user():
    """获取当前登录用户；user 不存在时由 require_current_user 直接 abort 401。"""
    return require_current_user()


# ==================== 证书数据接口 ====================

@certificate_bp.route('/data', methods=['GET'])
@jwt_required()
def certificate_data():
    """获取证书数据"""
    user_id = int(get_jwt_identity())
    project_id = request.args.get('projectId', type=int)
    if not project_id:
        return error('缺少项目ID')

    try:
        data = certificate_service.get_certificate_data(user_id, project_id)
        log_operation(user_id, 'generate_certificate', 'project', project_id,
                      f'查看证书：{data["projectTitle"]}')
        return success(data=data)
    except ValueError as e:
        return error(str(e))


@certificate_bp.route('/my-list', methods=['GET'])
@jwt_required()
def my_certificate_list():
    """可获得证书的项目列表"""
    user_id = int(get_jwt_identity())
    data = certificate_service.get_my_certificate_list(user_id)
    return success(data=data)


# ==================== 证书 PDF 下载 ====================

@certificate_bp.route('/render', methods=['POST'])
@jwt_required()
def certificate_pdf():
    """下载单张证书 PDF（学生本人或管理员）。

    POST body 支持字段：
      - projectId (必填)
      - userId (可选，仅管理员可指定)
      - commendationText (可选，自定义表彰语，例如 AI 生成内容)

    端点命名为 /render 而非 /pdf，规避部分浏览器隐私扩展对 *pdf 路径的默认拦截。
    """
    user = _get_current_user()
    body = request.get_json() or {}
    project_id = body.get('projectId')
    if not project_id:
        return error('缺少项目ID')

    target_user_id = body.get('userId') or user.id
    if target_user_id != user.id and user.role != 'admin':
        return error('无权下载其他用户的证书', 403)

    commendation_text = body.get('commendationText') or None

    try:
        data = certificate_service.get_certificate_data(target_user_id, project_id)
    except ValueError as e:
        return error(str(e))

    pdf_buf = cert_pdf_service.render_certificate_pdf(data, commendation_text=commendation_text)
    log_operation(user.id, 'generate_certificate', 'project', project_id,
                  f'下载证书PDF：{data["projectTitle"]} - {data["userName"]}')

    safe_name = data['userName'].replace('/', '_').replace('\\', '_')
    filename = f'{safe_name}_{data["studentId"]}_志愿服务证明.pdf'
    # mimetype 用通用二进制流，避免部分浏览器隐私 / 杀软扩展按 application/pdf 拦截 + 重发
    return send_file(
        pdf_buf,
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name=filename,
    )


@certificate_bp.route('/batch', methods=['POST'])
@jwt_required()
def batch_certificate_pdf():
    """按项目批量下载证书 ZIP（仅项目创建者或管理员）。端点命名规避浏览器扩展拦截。"""
    user = _get_current_user()
    data = request.get_json() or {}
    project_id = data.get('projectId')

    if not project_id:
        return error('缺少项目ID')

    project = Project.query.get(project_id)
    if not project:
        return error('项目不存在', 404)
    if user.role != 'admin' and project.creator_id != user.id:
        return error('只能批量导出自己创建的项目的证书', 403)

    try:
        zip_buf, filename = cert_pdf_service.render_batch_zip(project_id)
    except ValueError as e:
        return error(str(e))

    log_operation(user.id, 'generate_certificate', 'project', project_id,
                  f'批量导出证书：{project.title}')
    return send_file(
        zip_buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename,
    )


# ==================== 项目合格学生查询（保留供前端确认人数等用途） ====================

@certificate_bp.route('/eligible-users', methods=['GET'])
@jwt_required()
def eligible_users():
    """查询某项目可生成证书的学生（项目创建者 / 管理员）"""
    user = _get_current_user()
    project_id = request.args.get('projectId', type=int)
    if not project_id:
        return error('缺少项目ID')

    project = Project.query.get(project_id)
    if not project:
        return error('项目不存在', 404)
    if user.role != 'admin' and project.creator_id != user.id:
        return error('只能查看自己创建的项目', 403)

    user_ids = certificate_service.get_eligible_users(project_id)
    students = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    return success(data=[{
        'id': u.id,
        'realName': u.real_name,
        'studentId': u.student_id,
        'college': u.college_name,
    } for u in students])

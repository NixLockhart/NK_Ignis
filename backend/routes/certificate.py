from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.cert_template import CertTemplate
from models.user import User
from models.project import Project
from services import certificate_service, cert_pdf_service
from utils.response import success, error
from utils.log_util import log_operation

certificate_bp = Blueprint('certificate', __name__, url_prefix='/api/certificate')


def _get_current_user():
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


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

@certificate_bp.route('/pdf', methods=['GET'])
@jwt_required()
def certificate_pdf():
    """下载单张证书 PDF（学生本人或管理员）"""
    user = _get_current_user()
    project_id = request.args.get('projectId', type=int)
    if not project_id:
        return error('缺少项目ID')

    target_user_id = request.args.get('userId', type=int) or user.id
    if target_user_id != user.id and user.role != 'admin':
        return error('无权下载其他用户的证书', 403)

    template_id = request.args.get('templateId', type=int)
    template = None
    if template_id:
        template = CertTemplate.query.get(template_id)
    if not template:
        template = CertTemplate.query.filter_by(is_default=True, enabled=True).first()
    if not template:
        template = CertTemplate.query.filter_by(enabled=True).first()
    if not template:
        return error('未找到可用证书模板，请先在模板管理中启用至少一个模板')

    try:
        data = certificate_service.get_certificate_data(target_user_id, project_id)
    except ValueError as e:
        return error(str(e))

    pdf_buf = cert_pdf_service.render_certificate_pdf(data, template)
    log_operation(user.id, 'generate_certificate', 'project', project_id,
                  f'下载证书PDF：{data["projectTitle"]} - {data["userName"]}')

    safe_name = data['userName'].replace('/', '_').replace('\\', '_')
    filename = f'{safe_name}_{data["studentId"]}_志愿服务证明.pdf'
    return send_file(
        pdf_buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    )


@certificate_bp.route('/batch-pdf', methods=['POST'])
@jwt_required()
def batch_certificate_pdf():
    """按项目批量下载证书 ZIP（仅项目创建者或管理员）"""
    user = _get_current_user()
    data = request.get_json() or {}
    project_id = data.get('projectId')
    template_id = data.get('templateId')

    if not project_id:
        return error('缺少项目ID')

    project = Project.query.get(project_id)
    if not project:
        return error('项目不存在', 404)
    if user.role != 'admin' and project.creator_id != user.id:
        return error('只能批量导出自己创建的项目的证书', 403)

    try:
        zip_buf, filename = cert_pdf_service.render_batch_zip(project_id, template_id)
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


# ==================== 证书模板管理 ====================

@certificate_bp.route('/templates', methods=['GET'])
@jwt_required()
def list_templates():
    """模板列表（所有登录用户可读，前端选择用）"""
    only_enabled = request.args.get('enabled', 'true').lower() == 'true'
    query = CertTemplate.query
    if only_enabled:
        query = query.filter_by(enabled=True)
    templates = query.order_by(CertTemplate.is_default.desc(), CertTemplate.id).all()
    return success(data=[t.to_dict() for t in templates])


@certificate_bp.route('/template', methods=['POST'])
@jwt_required()
def create_template():
    """创建模板（仅管理员）"""
    user = _get_current_user()
    if user.role != 'admin':
        return error('仅管理员可操作', 403)

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return error('模板名称不能为空')
    if CertTemplate.query.filter_by(name=name).first():
        return error('该模板名称已存在')

    t = CertTemplate(
        name=name,
        bg_color=data.get('bgColor', '#F8FAFB'),
        accent_color=data.get('accentColor', '#4F6EF7'),
        signature_text=data.get('signatureText', '高校青年志愿者服务中心'),
        commendation_style=data.get('commendationStyle', 'formal'),
        enabled=bool(data.get('enabled', True)),
        is_default=False,
    )
    db.session.add(t)
    db.session.commit()
    log_operation(user.id, 'generate_certificate', 'cert_template', t.id,
                  f'创建证书模板：{name}')
    return success(data=t.to_dict(), message='添加成功')


@certificate_bp.route('/template/<int:template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    """修改模板（仅管理员）"""
    user = _get_current_user()
    if user.role != 'admin':
        return error('仅管理员可操作', 403)

    t = CertTemplate.query.get(template_id)
    if not t:
        return error('模板不存在', 404)

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if name and name != t.name:
        if CertTemplate.query.filter_by(name=name).first():
            return error('该模板名称已存在')
        t.name = name
    if 'bgColor' in data:
        t.bg_color = data['bgColor']
    if 'accentColor' in data:
        t.accent_color = data['accentColor']
    if 'signatureText' in data:
        t.signature_text = data['signatureText']
    if 'commendationStyle' in data:
        t.commendation_style = data['commendationStyle']
    if 'enabled' in data:
        t.enabled = bool(data['enabled'])
    if data.get('isDefault'):
        # 同一时间只允许一个默认
        CertTemplate.query.filter(CertTemplate.id != template_id).update(
            {'is_default': False}
        )
        t.is_default = True

    db.session.commit()
    log_operation(user.id, 'generate_certificate', 'cert_template', t.id,
                  f'修改证书模板：{t.name}')
    return success(data=t.to_dict(), message='修改成功')


@certificate_bp.route('/template/<int:template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    """删除模板（仅管理员，默认模板禁止删除）"""
    user = _get_current_user()
    if user.role != 'admin':
        return error('仅管理员可操作', 403)

    t = CertTemplate.query.get(template_id)
    if not t:
        return error('模板不存在', 404)
    if t.is_default:
        return error('默认模板不可删除，请先切换其他模板为默认', 400)

    db.session.delete(t)
    db.session.commit()
    log_operation(user.id, 'generate_certificate', 'cert_template', template_id,
                  f'删除证书模板：{t.name}')
    return success(message='删除成功')


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

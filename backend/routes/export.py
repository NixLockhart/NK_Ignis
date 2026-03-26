from flask import Blueprint, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import export_service
from utils.response import error
from utils.log_util import log_operation
from models.user import User
from models.project import Project

export_bp = Blueprint('export', __name__, url_prefix='/api/export')


def _get_current_user():
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


@export_bp.route('/applications', methods=['GET'])
@jwt_required()
def export_applications():
    """导出某项目报名名单"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)

    from flask import request
    project_id = request.args.get('projectId', type=int)
    if not project_id:
        return error('缺少项目ID')

    # 负责人只能导出自己项目
    project = Project.query.get(project_id)
    if not project:
        return error('项目不存在', 404)
    if user.role != 'admin' and project.creator_id != user.id:
        return error('只能导出自己创建的项目', 403)

    try:
        buf, filename = export_service.export_application_list(project_id)
        log_operation(user.id, 'export_applications', 'project', project_id,
                      f'导出报名名单：{project.title}')
        return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=filename)
    except ValueError as e:
        return error(str(e))


@export_bp.route('/project-stats', methods=['GET'])
@jwt_required()
def export_project_stats():
    """导出项目统计数据"""
    user = _get_current_user()
    if user.role != 'admin':
        return error('仅管理员可导出', 403)

    buf, filename = export_service.export_project_stats()
    log_operation(user.id, 'export_project_stats', None, None, '导出项目统计数据')
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)


@export_bp.route('/hours-records', methods=['GET'])
@jwt_required()
def export_hours_records():
    """导出志愿者时长记录"""
    user = _get_current_user()
    if user.role != 'admin':
        return error('仅管理员可导出', 403)

    buf, filename = export_service.export_hours_records()
    log_operation(user.id, 'export_hours_records', None, None, '导出时长记录')
    return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)

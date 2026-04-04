from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import application_service
from utils.response import success, error
from utils.log_util import log_operation
from models.user import User
from models.project import Project

application_bp = Blueprint('application', __name__, url_prefix='/api/application')


def _get_current_user():
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


@application_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply():
    """学生报名"""
    user = _get_current_user()
    data = request.get_json()
    project_id = data.get('projectId') if data else None
    if not project_id:
        return error('缺少项目ID')

    try:
        app = application_service.apply_project(
            user.id, project_id, data.get('applyReason', ''),
        )
        log_operation(user.id, 'apply_project', 'application', app.id,
                      f'报名项目：{app.project.title}')
        return success(data=app.to_dict(), message='报名成功')
    except ValueError as e:
        return error(str(e))


@application_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel():
    """取消报名"""
    user = _get_current_user()
    data = request.get_json()
    app_id = data.get('id') if data else None
    if not app_id:
        return error('缺少报名ID')

    try:
        app = application_service.cancel_application(app_id, user.id)
        log_operation(user.id, 'cancel_application', 'application', app.id, '取消报名')
        return success(message='已取消报名')
    except PermissionError as e:
        return error(str(e), 403)
    except ValueError as e:
        return error(str(e))


@application_bp.route('/approve', methods=['POST'])
@jwt_required()
def approve():
    """通过报名（负责人，校验名额）"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)

    data = request.get_json()
    app_id = data.get('id') if data else None
    if not app_id:
        return error('缺少报名ID')

    try:
        app = application_service.approve_application(app_id, user.id)
        log_operation(user.id, 'approve_application', 'application', app.id,
                      f'通过报名：{app.user.real_name} → {app.project.title}')
        return success(data=app.to_dict(), message='已通过')
    except PermissionError as e:
        return error(str(e), 403)
    except ValueError as e:
        return error(str(e))


@application_bp.route('/reject', methods=['POST'])
@jwt_required()
def reject():
    """拒绝报名"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)

    data = request.get_json()
    app_id = data.get('id') if data else None
    remark = data.get('remark', '') if data else ''
    if not app_id:
        return error('缺少报名ID')

    try:
        app = application_service.reject_application(app_id, user.id, remark)
        log_operation(user.id, 'reject_application', 'application', app.id,
                      f'拒绝报名：{app.user.real_name}')
        return success(data=app.to_dict(), message='已拒绝')
    except PermissionError as e:
        return error(str(e), 403)
    except ValueError as e:
        return error(str(e))


@application_bp.route('/batch-approve', methods=['POST'])
@jwt_required()
def batch_approve():
    """批量通过报名"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)
    data = request.get_json()
    ids = data.get('ids', []) if data else []
    if not ids:
        return error('请选择报名记录')
    ok, fail = 0, 0
    for aid in ids:
        try:
            application_service.approve_application(aid, user.id)
            ok += 1
        except Exception:
            fail += 1
    log_operation(user.id, 'approve_application', detail=f'批量通过{ok}条报名')
    return success(message=f'成功通过{ok}条，失败{fail}条')


@application_bp.route('/batch-reject', methods=['POST'])
@jwt_required()
def batch_reject():
    """批量拒绝报名"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)
    data = request.get_json()
    ids = data.get('ids', []) if data else []
    remark = data.get('remark', '批量拒绝')
    if not ids:
        return error('请选择报名记录')
    ok, fail = 0, 0
    for aid in ids:
        try:
            application_service.reject_application(aid, user.id, remark)
            ok += 1
        except Exception:
            fail += 1
    log_operation(user.id, 'reject_application', detail=f'批量拒绝{ok}条报名')
    return success(message=f'成功拒绝{ok}条，失败{fail}条')


@application_bp.route('/list', methods=['GET'])
@jwt_required()
def application_list():
    """某项目的报名列表（负责人视角）"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)

    project_id = request.args.get('projectId', type=int)
    if not project_id:
        return error('缺少项目ID')

    # 校验是否为项目创建者
    project = Project.query.get(project_id)
    if not project:
        return error('项目不存在', 404)
    if user.role != 'admin' and project.creator_id != user.id:
        return error('只能查看自己创建的项目的报名', 403)

    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)

    data = application_service.get_project_applications(
        project_id, status=status, page=page, page_size=page_size,
    )
    return success(data=data)


@application_bp.route('/my', methods=['GET'])
@jwt_required()
def my_applications():
    """我的报名记录"""
    user = _get_current_user()
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)

    data = application_service.get_my_applications(
        user.id, status=status, page=page, page_size=page_size,
    )
    return success(data=data)


@application_bp.route('/status', methods=['GET'])
@jwt_required()
def application_status():
    """查询报名状态（用于详情页按钮）"""
    user = _get_current_user()
    project_id = request.args.get('projectId', type=int)
    if not project_id:
        return error('缺少项目ID')

    data = application_service.get_application_status(project_id, user.id)
    return success(data=data)


@application_bp.route('/count', methods=['GET'])
@jwt_required()
def approved_count():
    """查询已通过人数"""
    project_id = request.args.get('projectId', type=int)
    if not project_id:
        return error('缺少项目ID')

    count = application_service.get_approved_count(project_id)
    return success(data={'approvedCount': count})

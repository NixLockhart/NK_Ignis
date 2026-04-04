from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import project_service
from utils.response import success, error
from utils.log_util import log_operation
from models.user import User

project_bp = Blueprint('project', __name__, url_prefix='/api/project')


def _get_current_user():
    """获取当前登录用户"""
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


@project_bp.route('/create', methods=['POST'])
@jwt_required()
def create():
    """创建项目（仅 leader）"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('只有志愿负责人可以创建项目', 403)

    data = request.get_json()
    if not data or not data.get('title'):
        return error('项目名称不能为空')

    try:
        project = project_service.create_project(user.id, data)
        log_operation(user.id, 'create_project', 'project', project.id,
                      f'创建项目：{project.title}')
        return success(data=project.to_dict(), message='创建成功')
    except ValueError as e:
        return error(str(e))


@project_bp.route('/update', methods=['PUT'])
@jwt_required()
def update():
    """编辑项目（仅创建者，仅草稿状态）"""
    user = _get_current_user()
    data = request.get_json()
    project_id = data.get('id') if data else None
    if not project_id:
        return error('缺少项目ID')

    try:
        project = project_service.update_project(project_id, user.id, data)
        log_operation(user.id, 'update_project', 'project', project.id,
                      f'编辑项目：{project.title}')
        return success(data=project.to_dict(), message='更新成功')
    except PermissionError as e:
        return error(str(e), 403)
    except ValueError as e:
        return error(str(e))


@project_bp.route('/delete', methods=['DELETE'])
@jwt_required()
def delete():
    """删除项目（逻辑删除，仅创建者，仅草稿）"""
    user = _get_current_user()
    project_id = request.args.get('id', type=int)
    if not project_id:
        return error('缺少项目ID')

    try:
        project_service.delete_project(project_id, user.id)
        log_operation(user.id, 'delete_project', 'project', project_id, '删除项目')
        return success(message='删除成功')
    except PermissionError as e:
        return error(str(e), 403)
    except ValueError as e:
        return error(str(e))


@project_bp.route('/submit', methods=['POST'])
@jwt_required()
def submit():
    """提交审核 draft → pending"""
    user = _get_current_user()
    data = request.get_json()
    project_id = data.get('id') if data else None
    if not project_id:
        return error('缺少项目ID')

    try:
        project = project_service.submit_for_review(project_id, user.id)
        log_operation(user.id, 'submit_project', 'project', project.id,
                      f'提交审核：{project.title}')
        return success(data=project.to_dict(), message='已提交审核')
    except PermissionError as e:
        return error(str(e), 403)
    except ValueError as e:
        return error(str(e))


@project_bp.route('/approve', methods=['POST'])
@jwt_required()
def approve():
    """审核通过 pending → published（仅 admin）"""
    user = _get_current_user()
    if user.role != 'admin':
        return error('只有管理员可以审核项目', 403)

    data = request.get_json()
    project_id = data.get('id') if data else None
    remark = data.get('remark', '') if data else ''
    if not project_id:
        return error('缺少项目ID')

    try:
        project = project_service.approve_project(project_id, remark)
        log_operation(user.id, 'approve_project', 'project', project.id,
                      f'审核通过：{project.title}')
        return success(data=project.to_dict(), message='审核通过')
    except ValueError as e:
        return error(str(e))


@project_bp.route('/reject', methods=['POST'])
@jwt_required()
def reject():
    """审核驳回 pending → draft（仅 admin）"""
    user = _get_current_user()
    if user.role != 'admin':
        return error('只有管理员可以审核项目', 403)

    data = request.get_json()
    project_id = data.get('id') if data else None
    remark = data.get('remark', '') if data else ''
    if not project_id:
        return error('缺少项目ID')

    try:
        project = project_service.reject_project(project_id, remark)
        log_operation(user.id, 'reject_project', 'project', project.id,
                      f'审核驳回：{project.title}，原因：{remark}')
        return success(data=project.to_dict(), message='已驳回')
    except ValueError as e:
        return error(str(e))


@project_bp.route('/batch-approve', methods=['POST'])
@jwt_required()
def batch_approve():
    """批量审核通过"""
    user = _get_current_user()
    if user.role != 'admin':
        return error('仅管理员可操作', 403)
    data = request.get_json()
    ids = data.get('ids', []) if data else []
    remark = data.get('remark', '')
    if not ids:
        return error('请选择项目')
    ok, fail = 0, 0
    for pid in ids:
        try:
            project_service.approve_project(pid, remark)
            ok += 1
        except Exception:
            fail += 1
    log_operation(user.id, 'approve_project', detail=f'批量审核通过{ok}个项目')
    return success(message=f'成功通过{ok}个，失败{fail}个')


@project_bp.route('/list', methods=['GET'])
@jwt_required()
def project_list():
    """项目列表（学生只看已发布，负责人/管理员看全部）"""
    user = _get_current_user()
    status = request.args.get('status')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)

    # 学生只能看已发布及之后状态
    published_only = (user.role == 'student')

    data = project_service.get_project_list(
        status=status, category=category,
        page=page, page_size=page_size,
        published_only=published_only,
    )
    return success(data=data)


@project_bp.route('/detail', methods=['GET'])
@jwt_required()
def detail():
    """项目详情"""
    project_id = request.args.get('id', type=int)
    if not project_id:
        return error('缺少项目ID')

    try:
        data = project_service.get_project_detail(project_id)
        return success(data=data)
    except ValueError as e:
        return error(str(e), 404)


@project_bp.route('/my', methods=['GET'])
@jwt_required()
def my_projects():
    """我创建的项目（仅 leader/admin）"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)

    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)

    data = project_service.get_my_projects(user.id, status=status, page=page, page_size=page_size)
    return success(data=data)

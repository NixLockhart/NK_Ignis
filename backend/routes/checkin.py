from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import checkin_service
from utils.response import success, error
from utils.log_util import log_operation
from utils.auth import require_current_user
from models.user import User
from models.project import Project

checkin_bp = Blueprint('checkin', __name__, url_prefix='/api/checkin')


def _get_current_user():
    """获取当前登录用户；user 不存在时由 require_current_user 直接 abort 401。"""
    return require_current_user()


@checkin_bp.route('/sign-in', methods=['POST'])
@jwt_required()
def sign_in():
    """签到（可携带 lat/lng 用于地理位置校验）"""
    user = _get_current_user()
    data = request.get_json() or {}
    project_id = data.get('projectId')
    if not project_id:
        return error('缺少项目ID')

    lat = data.get('lat')
    lng = data.get('lng')

    try:
        checkin = checkin_service.sign_in(user.id, project_id, lat=lat, lng=lng)
        log_operation(user.id, 'sign_in', 'checkin', checkin.id,
                      f'签到：{checkin.project.title}')
        return success(data=checkin.to_dict(), message='签到成功')
    except ValueError as e:
        return error(str(e))


@checkin_bp.route('/sign-out', methods=['POST'])
@jwt_required()
def sign_out():
    """签退（可携带 lat/lng 用于位置异常检测）"""
    user = _get_current_user()
    data = request.get_json() or {}
    project_id = data.get('projectId')
    if not project_id:
        return error('缺少项目ID')

    lat = data.get('lat')
    lng = data.get('lng')

    try:
        checkin = checkin_service.sign_out(user.id, project_id, lat=lat, lng=lng)
        log_operation(user.id, 'sign_out', 'checkin', checkin.id,
                      f'签退：{checkin.project.title}，时长{checkin.duration_hours}h')
        return success(data=checkin.to_dict(), message='签退成功')
    except ValueError as e:
        return error(str(e))


@checkin_bp.route('/confirm', methods=['POST'])
@jwt_required()
def confirm():
    """确认打卡"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)

    data = request.get_json()
    checkin_id = data.get('id') if data else None
    if not checkin_id:
        return error('缺少打卡ID')

    try:
        checkin = checkin_service.confirm_checkin(checkin_id, user.id)
        log_operation(user.id, 'confirm_checkin', 'checkin', checkin.id,
                      f'确认打卡：{checkin.user.real_name}，{checkin.duration_hours}h')
        return success(data=checkin.to_dict(), message='已确认')
    except PermissionError as e:
        return error(str(e), 403)
    except ValueError as e:
        return error(str(e))


@checkin_bp.route('/reject', methods=['POST'])
@jwt_required()
def reject():
    """驳回打卡"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)

    data = request.get_json()
    checkin_id = data.get('id') if data else None
    remark = data.get('remark', '') if data else ''
    if not checkin_id:
        return error('缺少打卡ID')

    try:
        checkin = checkin_service.reject_checkin(checkin_id, user.id, remark)
        log_operation(user.id, 'reject_checkin', 'checkin', checkin.id,
                      f'驳回打卡：{checkin.user.real_name}')
        return success(data=checkin.to_dict(), message='已驳回')
    except PermissionError as e:
        return error(str(e), 403)
    except ValueError as e:
        return error(str(e))


@checkin_bp.route('/batch-confirm', methods=['POST'])
@jwt_required()
def batch_confirm():
    """批量确认打卡"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)
    data = request.get_json()
    ids = data.get('ids', []) if data else []
    if not ids:
        return error('请选择打卡记录')
    ok, fail = 0, 0
    for cid in ids:
        try:
            checkin_service.confirm_checkin(cid, user.id)
            ok += 1
        except Exception:
            fail += 1
    log_operation(user.id, 'confirm_checkin', detail=f'批量确认{ok}条打卡')
    return success(message=f'成功确认{ok}条，失败{fail}条')


@checkin_bp.route('/batch-reject', methods=['POST'])
@jwt_required()
def batch_reject():
    """批量驳回打卡"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)
    data = request.get_json()
    ids = data.get('ids', []) if data else []
    remark = data.get('remark', '批量驳回')
    if not ids:
        return error('请选择打卡记录')
    ok, fail = 0, 0
    for cid in ids:
        try:
            checkin_service.reject_checkin(cid, user.id, remark)
            ok += 1
        except Exception:
            fail += 1
    log_operation(user.id, 'reject_checkin', detail=f'批量驳回{ok}条打卡')
    return success(message=f'成功驳回{ok}条，失败{fail}条')


@checkin_bp.route('/list', methods=['GET'])
@jwt_required()
def checkin_list():
    """某项目打卡列表（负责人视角）"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)

    project_id = request.args.get('projectId', type=int)
    if not project_id:
        return error('缺少项目ID')

    project = Project.query.get(project_id)
    if not project:
        return error('项目不存在', 404)
    if user.role != 'admin' and project.creator_id != user.id:
        return error('只能查看自己创建的项目', 403)

    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)

    data = checkin_service.get_project_checkins(project_id, status=status, page=page, page_size=page_size)
    return success(data=data)


@checkin_bp.route('/my', methods=['GET'])
@jwt_required()
def my_checkins():
    """我的打卡记录"""
    user = _get_current_user()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)

    data = checkin_service.get_my_checkins(user.id, page=page, page_size=page_size)
    return success(data=data)


@checkin_bp.route('/total-hours', methods=['GET'])
@jwt_required()
def total_hours():
    """累计已确认时长"""
    user = _get_current_user()
    user_id = request.args.get('userId', type=int)
    if user_id and user_id != user.id and user.role != 'admin':
        return error('无权查询其他用户数据', 403)
    if not user_id:
        user_id = user.id

    hours = checkin_service.get_user_total_hours(user_id)
    return success(data={'totalHours': hours})


@checkin_bp.route('/hours-detail', methods=['GET'])
@jwt_required()
def hours_detail():
    """各项目时长明细"""
    user = _get_current_user()
    user_id = request.args.get('userId', type=int)
    if user_id and user_id != user.id and user.role != 'admin':
        return error('无权查询其他用户数据', 403)
    if not user_id:
        user_id = user.id

    data = checkin_service.get_user_hours_detail(user_id)
    return success(data=data)


@checkin_bp.route('/status', methods=['GET'])
@jwt_required()
def checkin_status():
    """查询打卡状态（用于详情页按钮）"""
    user = _get_current_user()
    project_id = request.args.get('projectId', type=int)
    if not project_id:
        return error('缺少项目ID')

    data = checkin_service.get_checkin_status(project_id, user.id)
    return success(data=data)

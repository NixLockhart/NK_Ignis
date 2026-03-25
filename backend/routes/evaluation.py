from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import evaluation_service
from utils.response import success, error
from utils.log_util import log_operation
from models.user import User

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api/evaluation')


def _get_current_user():
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


@evaluation_bp.route('/create', methods=['POST'])
@jwt_required()
def create():
    """学生评价活动"""
    user = _get_current_user()
    data = request.get_json()
    if not data or not data.get('projectId') or not data.get('score'):
        return error('缺少必要参数')

    try:
        ev = evaluation_service.create_evaluation(
            user.id, data['projectId'], int(data['score']), data.get('content', ''),
        )
        log_operation(user.id, 'create_evaluation', 'evaluation', ev.id,
                      f'评价项目：{ev.project.title}，{ev.score}分')
        return success(data=ev.to_dict(), message='评价成功')
    except ValueError as e:
        return error(str(e))


@evaluation_bp.route('/leader-comment', methods=['POST'])
@jwt_required()
def leader_comment():
    """负责人评价学生"""
    user = _get_current_user()
    if user.role not in ('leader', 'admin'):
        return error('无权限', 403)

    data = request.get_json()
    if not data or not data.get('projectId') or not data.get('targetUserId') or not data.get('score'):
        return error('缺少必要参数')

    try:
        ev = evaluation_service.create_leader_comment(
            user.id, data['projectId'], data['targetUserId'],
            int(data['score']), data.get('content', ''),
        )
        log_operation(user.id, 'leader_comment', 'evaluation', ev.id,
                      f'评价学生：{ev.target_user.real_name}')
        return success(data=ev.to_dict(), message='评价成功')
    except PermissionError as e:
        return error(str(e), 403)
    except ValueError as e:
        return error(str(e))


@evaluation_bp.route('/list', methods=['GET'])
@jwt_required()
def evaluation_list():
    """某项目评价列表"""
    project_id = request.args.get('projectId', type=int)
    if not project_id:
        return error('缺少项目ID')

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    data = evaluation_service.get_project_evaluations(project_id, page, page_size)
    return success(data=data)


@evaluation_bp.route('/my', methods=['GET'])
@jwt_required()
def my_evaluations():
    """我的评价记录"""
    user = _get_current_user()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 10, type=int)
    data = evaluation_service.get_my_evaluations(user.id, page, page_size)
    return success(data=data)

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import log_service
from utils.response import success, error
from models.user import User

log_bp = Blueprint('log', __name__, url_prefix='/api/log')


@log_bp.route('/list', methods=['GET'])
@jwt_required()
def log_list():
    """操作日志列表（仅 admin）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if user.role != 'admin':
        return error('仅管理员可查看日志', 403)

    action = request.args.get('action')
    target_user_id = request.args.get('userId', type=int)
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)

    data = log_service.get_logs(
        action=action, user_id=target_user_id,
        start_date=start_date, end_date=end_date,
        page=page, page_size=page_size,
    )
    return success(data=data)

from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import statistics_service
from utils.response import success, error
from models.user import User

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')


def _get_current_user():
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)


def _require_admin():
    user = _get_current_user()
    if user.role != 'admin':
        return None, error('仅管理员可查看统计数据', 403)
    return user, None


@statistics_bp.route('/overview', methods=['GET'])
@jwt_required()
def overview():
    user, err = _require_admin()
    if err:
        return err
    return success(data=statistics_service.get_overview_stats())


@statistics_bp.route('/category', methods=['GET'])
@jwt_required()
def category():
    user, err = _require_admin()
    if err:
        return err
    return success(data=statistics_service.get_project_category_stats())


@statistics_bp.route('/college', methods=['GET'])
@jwt_required()
def college():
    user, err = _require_admin()
    if err:
        return err
    return success(data=statistics_service.get_college_participation_stats())


@statistics_bp.route('/monthly-hours', methods=['GET'])
@jwt_required()
def monthly_hours():
    user, err = _require_admin()
    if err:
        return err
    return success(data=statistics_service.get_monthly_hours_trend())


@statistics_bp.route('/applications', methods=['GET'])
@jwt_required()
def applications():
    user, err = _require_admin()
    if err:
        return err
    return success(data=statistics_service.get_project_application_stats())


@statistics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    """控制台统计数据（所有角色可访问）"""
    user = _get_current_user()
    return success(data=statistics_service.get_dashboard_stats(user.id, user.role))

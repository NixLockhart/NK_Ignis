from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import statistics_service
from utils.response import success, error
from utils.auth import require_current_user
from models.user import User

statistics_bp = Blueprint('statistics', __name__, url_prefix='/api/statistics')


def _get_current_user():
    """获取当前登录用户；user 不存在时由 require_current_user 直接 abort 401。"""
    return require_current_user()


def _require_admin():
    user = _get_current_user()
    if user.role != 'admin':
        return None, error('仅管理员可查看统计数据', 403)
    return user, None


def _filter_args():
    """从 query string 抽取筛选参数（startDate / endDate / collegeId / category）"""
    return {
        'start_date': request.args.get('startDate') or None,
        'end_date': request.args.get('endDate') or None,
        'college_id': request.args.get('collegeId', type=int),
        'category': request.args.get('category') or None,
    }


@statistics_bp.route('/overview', methods=['GET'])
@jwt_required()
def overview():
    user, err = _require_admin()
    if err:
        return err
    return success(data=statistics_service.get_overview_stats(**_filter_args()))


@statistics_bp.route('/category', methods=['GET'])
@jwt_required()
def category():
    user, err = _require_admin()
    if err:
        return err
    return success(data=statistics_service.get_project_category_stats(**_filter_args()))


@statistics_bp.route('/college', methods=['GET'])
@jwt_required()
def college():
    user, err = _require_admin()
    if err:
        return err
    return success(data=statistics_service.get_college_participation_stats(**_filter_args()))


@statistics_bp.route('/monthly-hours', methods=['GET'])
@jwt_required()
def monthly_hours():
    user, err = _require_admin()
    if err:
        return err
    return success(data=statistics_service.get_monthly_hours_trend(**_filter_args()))


@statistics_bp.route('/applications', methods=['GET'])
@jwt_required()
def applications():
    user, err = _require_admin()
    if err:
        return err
    return success(data=statistics_service.get_project_application_stats(**_filter_args()))


@statistics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    """控制台统计数据（所有角色可访问）"""
    user = _get_current_user()
    return success(data=statistics_service.get_dashboard_stats(user.id, user.role))


@statistics_bp.route('/drill', methods=['GET'])
@jwt_required()
def drill():
    """统计明细下钻（仅管理员）

    必填参数：
      - dimension: 'college' / 'category' / 'month'
      - value:     维度对应取值（学院名 / 类型名 / 'YYYY-MM'）
    可选参数：
      - startDate / endDate / collegeId / category（与图表筛选保持一致）
    """
    user, err = _require_admin()
    if err:
        return err

    dimension = request.args.get('dimension')
    value = request.args.get('value')
    if dimension not in ('college', 'category', 'month'):
        return error('维度参数无效，应为 college / category / month')
    if not value:
        return error('缺少 value 参数')

    data = statistics_service.drill_down(
        dimension=dimension, value=value, **_filter_args()
    )
    return success(data=data)

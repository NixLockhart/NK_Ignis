from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from sqlalchemy import func
from models import db
from models.checkin import Checkin
from models.application import Application
from models.project import Project

# 异常时长阈值（小时）
ABNORMAL_THRESHOLD = 0.5
# 异常超长阈值（小时）— 单次连续打卡超过 24h 视为异常
DURATION_TOO_LONG_THRESHOLD = 24


def _haversine_distance_m(lat1, lng1, lat2, lng2):
    """计算两点间距离（米），使用 Haversine 公式"""
    R = 6371000  # 地球平均半径（米）
    lat1_rad, lat2_rad = radians(lat1), radians(lat2)
    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = sin(d_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(d_lng / 2) ** 2
    return 2 * R * asin(sqrt(a))


def _validate_sign_in_window(project, now=None):
    """时间窗校验：允许在项目开始前 window 分钟到结束后 window 分钟之间签到"""
    if now is None:
        now = datetime.now()
    window = timedelta(minutes=project.sign_in_window_minutes or 30)
    if project.start_time and now < project.start_time - window:
        return False, '当前距离项目开始时间过早，无法签到'
    if project.end_time and now > project.end_time + window:
        return False, '当前已超出项目结束时间，无法签到'
    return True, None


def _validate_sign_in_location(project, lat, lng):
    """位置校验：若项目设置了坐标，签到位置必须在 radius_m 米内"""
    if project.lat is None or project.lng is None:
        return True, None  # 项目未配置坐标，跳过位置校验
    if lat is None or lng is None:
        return False, '请允许获取位置信息后再签到'
    radius = project.radius_m or 200
    distance = _haversine_distance_m(project.lat, project.lng, lat, lng)
    if distance > radius:
        return False, f'签到位置偏离项目地点 {int(distance)} 米，超出允许范围（{radius} 米）'
    return True, None


def sign_in(user_id, project_id, lat=None, lng=None):
    """签到（含时间窗 + 地理位置 + 报名状态三重验证）"""
    project = Project.query.get(project_id)
    if not project or project.is_deleted:
        raise ValueError('项目不存在')

    # 校验是否已通过报名
    approved = Application.query.filter_by(
        project_id=project_id, user_id=user_id, status='approved'
    ).first()
    if not approved:
        raise ValueError('您未通过该项目的报名，无法签到')

    # 校验是否已有未签退的记录
    active = Checkin.query.filter_by(
        project_id=project_id, user_id=user_id, sign_out_time=None
    ).first()
    if active:
        raise ValueError('您已签到，请先签退')

    # 校验是否已有完成的打卡记录（一个项目一人只能打卡一次）
    # 排除已被驳回的记录 —— 否则被驳回后学生永远无法重新签到
    completed = Checkin.query.filter_by(
        project_id=project_id, user_id=user_id
    ).filter(
        Checkin.sign_out_time.isnot(None),
        Checkin.status != 'rejected',
    ).first()
    if completed:
        raise ValueError('您已完成该项目的打卡，不能重复签到')

    # ====== 三重验证之一：时间窗 ======
    ok, err_msg = _validate_sign_in_window(project)
    if not ok:
        raise ValueError(err_msg)

    # ====== 三重验证之二：地理位置 ======
    ok, err_msg = _validate_sign_in_location(project, lat, lng)
    if not ok:
        raise ValueError(err_msg)

    checkin = Checkin(
        project_id=project_id,
        user_id=user_id,
        sign_in_time=datetime.now(),
        status='pending',
    )
    db.session.add(checkin)
    db.session.commit()
    return checkin


def sign_out(user_id, project_id, lat=None, lng=None):
    """签退（自动计算时长 + 异常检测分类）"""
    checkin = Checkin.query.filter_by(
        project_id=project_id, user_id=user_id, sign_out_time=None
    ).first()
    if not checkin:
        raise ValueError('您尚未签到或已签退')

    checkin.sign_out_time = datetime.now()

    # 计算时长
    delta = (checkin.sign_out_time - checkin.sign_in_time).total_seconds() / 3600
    checkin.duration_hours = round(delta, 2)

    # ====== 异常检测分类（按优先级覆盖：位置 > 时间窗 > 时长） ======
    project = checkin.project
    abnormal_reason = None

    # 位置校验（如果项目有坐标且学生提供了坐标）
    if project and project.lat is not None and project.lng is not None \
            and lat is not None and lng is not None:
        distance = _haversine_distance_m(project.lat, project.lng, lat, lng)
        if distance > (project.radius_m or 200):
            abnormal_reason = 'location'

    # 签退时间窗（项目结束后超过 window 才签退视为异常）
    if abnormal_reason is None and project and project.end_time:
        window = timedelta(minutes=project.sign_in_window_minutes or 30)
        if checkin.sign_out_time > project.end_time + window:
            abnormal_reason = 'time_window'

    # 时长过短 / 过长
    if abnormal_reason is None:
        if checkin.duration_hours < ABNORMAL_THRESHOLD:
            abnormal_reason = 'duration_too_short'
        elif checkin.duration_hours > DURATION_TOO_LONG_THRESHOLD:
            abnormal_reason = 'duration_too_long'

    if abnormal_reason:
        checkin.is_abnormal = True
        checkin.abnormal_reason = abnormal_reason

    db.session.commit()
    return checkin


def confirm_checkin(checkin_id, leader_id):
    """负责人确认打卡"""
    checkin = _get_checkin_or_raise(checkin_id)
    project = checkin.project

    if project.creator_id != leader_id:
        raise PermissionError('只能确认自己创建的项目的打卡记录')
    if checkin.status != 'pending':
        raise ValueError('只有待确认状态的记录可以操作')
    if not checkin.sign_out_time:
        raise ValueError('该学生尚未签退，无法确认')

    checkin.status = 'confirmed'
    checkin.checked_by = leader_id
    checkin.checked_time = datetime.now()
    db.session.commit()
    return checkin


def reject_checkin(checkin_id, leader_id, remark=None):
    """负责人驳回打卡"""
    checkin = _get_checkin_or_raise(checkin_id)
    project = checkin.project

    if project.creator_id != leader_id:
        raise PermissionError('只能操作自己创建的项目的打卡记录')
    if checkin.status != 'pending':
        raise ValueError('只有待确认状态的记录可以操作')

    checkin.status = 'rejected'
    checkin.remark = remark
    checkin.checked_by = leader_id
    checkin.checked_time = datetime.now()
    db.session.commit()
    return checkin


def get_project_checkins(project_id, status=None, page=1, page_size=10):
    """某项目的打卡列表"""
    query = Checkin.query.filter_by(project_id=project_id)
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Checkin.sign_in_time.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return {
        'list': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size,
    }


def get_my_checkins(user_id, page=1, page_size=10):
    """我的打卡记录"""
    query = Checkin.query.filter_by(user_id=user_id)
    query = query.order_by(Checkin.sign_in_time.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return {
        'list': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size,
    }


def get_user_total_hours(user_id):
    """个人累计已确认时长"""
    result = db.session.query(
        func.sum(Checkin.duration_hours)
    ).filter_by(user_id=user_id, status='confirmed').scalar()
    return round(result or 0, 2)


def get_user_hours_detail(user_id):
    """各项目时长明细"""
    checkins = Checkin.query.filter_by(
        user_id=user_id, status='confirmed'
    ).all()
    return [{
        'projectId': c.project_id,
        'projectTitle': c.project.title if c.project else None,
        'durationHours': c.duration_hours,
        'signInTime': c.sign_in_time.isoformat() if c.sign_in_time else None,
        'signOutTime': c.sign_out_time.isoformat() if c.sign_out_time else None,
    } for c in checkins]


def get_checkin_status(project_id, user_id):
    """查询某用户在某项目的打卡状态（用于详情页按钮渲染）"""
    checkin = Checkin.query.filter_by(
        project_id=project_id, user_id=user_id
    ).order_by(Checkin.id.desc()).first()
    if not checkin:
        return None
    return checkin.to_dict()


def _get_checkin_or_raise(checkin_id):
    checkin = Checkin.query.get(checkin_id)
    if not checkin:
        raise ValueError('打卡记录不存在')
    return checkin

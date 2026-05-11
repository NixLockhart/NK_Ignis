from datetime import datetime
from sqlalchemy import func, extract
from models import db
from models.project import Project
from models.application import Application
from models.checkin import Checkin
from models.user import User
from models.college import College


# ==================== 内部工具 ====================

def _parse_date(s):
    """将 'YYYY-MM-DD' 解析为 datetime；解析失败返回 None。"""
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    try:
        return datetime.strptime(str(s)[:10], '%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def _project_filters(query, start_date=None, end_date=None, category=None):
    """对项目相关查询追加日期与类型筛选。"""
    sd = _parse_date(start_date)
    ed = _parse_date(end_date)
    if sd:
        query = query.filter(Project.start_time >= sd)
    if ed:
        query = query.filter(Project.start_time <= ed)
    if category:
        query = query.filter(Project.category == category)
    return query


def _checkin_date_filters(query, start_date=None, end_date=None):
    """对打卡相关查询追加日期筛选（按 sign_in_time）。"""
    sd = _parse_date(start_date)
    ed = _parse_date(end_date)
    if sd:
        query = query.filter(Checkin.sign_in_time >= sd)
    if ed:
        query = query.filter(Checkin.sign_in_time <= ed)
    return query


# ==================== 主统计接口 ====================

def get_overview_stats(start_date=None, end_date=None, college_id=None, category=None):
    """总览数据（支持按时间区间 / 学院 / 项目类型筛选）"""
    project_q = Project.query.filter_by(is_deleted=False)
    project_q = _project_filters(project_q, start_date, end_date, category)
    project_count = project_q.count()

    # 志愿者数：在匹配项目里有 approved 报名的不同 user 数
    volunteer_q = db.session.query(func.count(func.distinct(Application.user_id))).join(
        Project, Application.project_id == Project.id
    ).filter(
        Application.status == 'approved',
        Project.is_deleted == False,
    )
    volunteer_q = _project_filters(volunteer_q, start_date, end_date, category)
    if college_id:
        volunteer_q = volunteer_q.join(User, User.id == Application.user_id).filter(
            User.college_id == college_id
        )
    volunteer_count = volunteer_q.scalar() or 0

    # 累计已确认时长（按筛选后的项目 + 学院过滤）
    hours_q = db.session.query(func.sum(Checkin.duration_hours)).join(
        Project, Checkin.project_id == Project.id
    ).filter(
        Checkin.status == 'confirmed',
        Project.is_deleted == False,
    )
    hours_q = _project_filters(hours_q, start_date, end_date, category)
    if college_id:
        hours_q = hours_q.join(User, User.id == Checkin.user_id).filter(
            User.college_id == college_id
        )
    total_hours = hours_q.scalar() or 0

    # 报名数（不含 cancelled）
    app_q = db.session.query(func.count(Application.id)).join(
        Project, Application.project_id == Project.id
    ).filter(
        Application.status != 'cancelled',
        Project.is_deleted == False,
    )
    app_q = _project_filters(app_q, start_date, end_date, category)
    if college_id:
        app_q = app_q.join(User, User.id == Application.user_id).filter(
            User.college_id == college_id
        )
    application_count = app_q.scalar() or 0

    return {
        'projectCount': project_count,
        'volunteerCount': volunteer_count,
        'totalHours': round(total_hours, 2),
        'applicationCount': application_count,
    }


def get_project_category_stats(start_date=None, end_date=None, college_id=None, category=None):
    """各类项目数量（饼图/柱状图）— 按筛选条件聚合"""
    q = db.session.query(
        Project.category, func.count(Project.id)
    ).filter(
        Project.is_deleted == False,
        Project.category.isnot(None),
        Project.category != '',
    )
    q = _project_filters(q, start_date, end_date, category)
    # 学院维度通过 approved 报名人侧关联
    if college_id:
        q = q.join(Application, Application.project_id == Project.id).join(
            User, User.id == Application.user_id
        ).filter(
            Application.status == 'approved',
            User.college_id == college_id,
        )
    results = q.group_by(Project.category).all()
    return {
        'categories': [r[0] for r in results],
        'counts': [r[1] for r in results],
    }


def get_college_participation_stats(start_date=None, end_date=None, college_id=None, category=None):
    """各学院参与人数（柱状图）— 优先按 college_id join，旧字符串字段做 fallback"""
    college_label = func.coalesce(College.name, User.college).label('college_label')
    q = db.session.query(
        college_label,
        func.count(func.distinct(Application.user_id))
    ).join(Application, Application.user_id == User.id) \
     .outerjoin(College, College.id == User.college_id) \
     .join(Project, Application.project_id == Project.id) \
     .filter(
        Application.status == 'approved',
        Project.is_deleted == False,
    )
    q = _project_filters(q, start_date, end_date, category)
    if college_id:
        q = q.filter(User.college_id == college_id)
    q = q.group_by(college_label).order_by(
        func.count(func.distinct(Application.user_id)).desc()
    )
    results = q.all()
    return {
        'colleges': [r[0] for r in results],
        'counts': [r[1] for r in results],
    }


def get_monthly_hours_trend(start_date=None, end_date=None, college_id=None, category=None):
    """每月服务时长趋势（折线图）"""
    q = db.session.query(
        extract('year', Checkin.sign_in_time).label('year'),
        extract('month', Checkin.sign_in_time).label('month'),
        func.sum(Checkin.duration_hours),
    ).join(Project, Checkin.project_id == Project.id) \
     .filter(
        Checkin.status == 'confirmed',
        Checkin.sign_in_time.isnot(None),
        Project.is_deleted == False,
    )
    q = _checkin_date_filters(q, start_date, end_date)
    if category:
        q = q.filter(Project.category == category)
    if college_id:
        q = q.join(User, User.id == Checkin.user_id).filter(User.college_id == college_id)

    results = q.group_by('year', 'month').order_by('year', 'month').all()
    return {
        'months': [f'{int(r[0])}-{int(r[1]):02d}' for r in results],
        'hours': [round(r[2] or 0, 2) for r in results],
    }


def get_project_application_stats(start_date=None, end_date=None, college_id=None, category=None):
    """各项目报名人数对比（柱状图，取前15个）"""
    q = db.session.query(
        Project.title, func.count(Application.id)
    ).join(Application, Application.project_id == Project.id).filter(
        Project.is_deleted == False,
        Application.status != 'cancelled',
    )
    q = _project_filters(q, start_date, end_date, category)
    if college_id:
        q = q.join(User, User.id == Application.user_id).filter(User.college_id == college_id)
    q = q.group_by(Project.id).order_by(func.count(Application.id).desc()).limit(15)
    results = q.all()
    return {
        'projects': [r[0] for r in results],
        'counts': [r[1] for r in results],
    }


def get_dashboard_stats(user_id, role):
    """控制台统计数据（按角色返回不同指标）"""
    if role == 'student':
        # 进行中的项目数（已通过报名且项目状态为 published/in_progress）
        active_projects = db.session.query(func.count(Application.id)).join(
            Project, Application.project_id == Project.id
        ).filter(
            Application.user_id == user_id,
            Application.status == 'approved',
            Project.status.in_(['published', 'in_progress']),
            Project.is_deleted == False,
        ).scalar() or 0

        # 累计已确认服务时长
        total_hours = db.session.query(
            func.sum(Checkin.duration_hours)
        ).filter_by(user_id=user_id, status='confirmed').scalar() or 0

        # 我的报名数（排除已取消）
        my_applications = Application.query.filter(
            Application.user_id == user_id,
            Application.status != 'cancelled',
        ).count()

        return {
            'cards': [
                {'title': '进行中的项目', 'value': active_projects, 'unit': '个', 'color': 'blue'},
                {'title': '累计服务时长', 'value': round(total_hours, 2), 'unit': '小时', 'color': 'green'},
                {'title': '我的报名', 'value': my_applications, 'unit': '次', 'color': 'orange'},
            ]
        }

    elif role == 'leader':
        # 我创建的项目数
        my_projects = Project.query.filter_by(
            creator_id=user_id, is_deleted=False
        ).count()

        # 我的项目总报名数
        my_project_ids = db.session.query(Project.id).filter_by(
            creator_id=user_id, is_deleted=False
        ).subquery()
        total_apps = Application.query.filter(
            Application.project_id.in_(my_project_ids),
            Application.status != 'cancelled',
        ).count()

        # 我的项目总签到数
        total_checkins = Checkin.query.filter(
            Checkin.project_id.in_(my_project_ids),
            Checkin.sign_out_time.isnot(None),
        ).count()

        return {
            'cards': [
                {'title': '我的项目', 'value': my_projects, 'unit': '个', 'color': 'blue'},
                {'title': '项目报名总数', 'value': total_apps, 'unit': '人次', 'color': 'green'},
                {'title': '项目签到总数', 'value': total_checkins, 'unit': '人次', 'color': 'orange'},
            ]
        }

    else:
        # 管理员：复用总览数据（不带筛选）
        stats = get_overview_stats()
        return {
            'cards': [
                {'title': '项目总数', 'value': stats['projectCount'], 'unit': '个', 'color': 'blue'},
                {'title': '志愿者人数', 'value': stats['volunteerCount'], 'unit': '人', 'color': 'green'},
                {'title': '累计总时长', 'value': stats['totalHours'], 'unit': '小时', 'color': 'orange'},
            ]
        }


# ==================== 下钻明细 ====================

def drill_down(dimension, value, start_date=None, end_date=None, college_id=None, category=None):
    """根据维度（college / category / month）返回明细列表。

    返回项目级别明细：项目名 / 类型 / 状态 / 报名数 / 签到人数 / 累计时长
    """
    q = db.session.query(
        Project.id, Project.title, Project.category, Project.status,
        Project.start_time, Project.end_time,
    ).filter(Project.is_deleted == False)
    q = _project_filters(q, start_date, end_date, category)

    if dimension == 'category' and value:
        q = q.filter(Project.category == value)
    elif dimension == 'college' and value:
        # 找出所有 approved 报名人里，college_name 等于 value 的项目
        sub = db.session.query(Application.project_id).join(
            User, User.id == Application.user_id
        ).outerjoin(College, College.id == User.college_id).filter(
            Application.status == 'approved',
            func.coalesce(College.name, User.college) == value,
        ).distinct().subquery()
        q = q.filter(Project.id.in_(sub))
    elif dimension == 'month' and value:
        # value 形如 '2026-04'，匹配 sign_in_time 落在该月的打卡所属项目
        try:
            y, m = value.split('-')
            y, m = int(y), int(m)
            sub = db.session.query(Checkin.project_id).filter(
                extract('year', Checkin.sign_in_time) == y,
                extract('month', Checkin.sign_in_time) == m,
                Checkin.status == 'confirmed',
            ).distinct().subquery()
            q = q.filter(Project.id.in_(sub))
        except (ValueError, AttributeError):
            return []

    if college_id and dimension != 'college':
        sub2 = db.session.query(Application.project_id).join(
            User, User.id == Application.user_id
        ).filter(
            Application.status == 'approved',
            User.college_id == college_id,
        ).distinct().subquery()
        q = q.filter(Project.id.in_(sub2))

    rows = q.order_by(Project.start_time.desc()).limit(100).all()

    # 为每个项目补统计（报名数 / 签到人数 / 累计时长）
    result = []
    for r in rows:
        approved_count = Application.query.filter_by(
            project_id=r.id, status='approved'
        ).count()
        confirmed_count = Checkin.query.filter_by(
            project_id=r.id, status='confirmed'
        ).count()
        hours = db.session.query(func.sum(Checkin.duration_hours)).filter_by(
            project_id=r.id, status='confirmed'
        ).scalar() or 0
        result.append({
            'projectId': r.id,
            'projectTitle': r.title,
            'category': r.category or '',
            'status': r.status,
            'startTime': r.start_time.isoformat() if r.start_time else None,
            'endTime': r.end_time.isoformat() if r.end_time else None,
            'approvedCount': approved_count,
            'confirmedCount': confirmed_count,
            'totalHours': round(hours, 2),
        })
    return result

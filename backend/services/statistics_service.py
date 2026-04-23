from sqlalchemy import func, extract
from models import db
from models.project import Project
from models.application import Application
from models.checkin import Checkin
from models.user import User


def get_overview_stats():
    """总览数据"""
    project_count = Project.query.filter_by(is_deleted=False).count()
    volunteer_count = User.query.filter_by(role='student').count()
    total_hours = db.session.query(
        func.sum(Checkin.duration_hours)
    ).filter_by(status='confirmed').scalar() or 0
    application_count = Application.query.filter(
        Application.status != 'cancelled'
    ).count()

    return {
        'projectCount': project_count,
        'volunteerCount': volunteer_count,
        'totalHours': round(total_hours, 2),
        'applicationCount': application_count,
    }


def get_project_category_stats():
    """各类项目数量（饼图/柱状图）"""
    results = db.session.query(
        Project.category, func.count(Project.id)
    ).filter(
        Project.is_deleted == False, Project.category.isnot(None), Project.category != ''
    ).group_by(Project.category).all()

    return {
        'categories': [r[0] for r in results],
        'counts': [r[1] for r in results],
    }


def get_college_participation_stats():
    """各学院参与人数（柱状图） — 优先按 college_id join，旧字符串字段做 fallback"""
    from models.college import College
    college_label = func.coalesce(College.name, User.college).label('college_label')
    results = db.session.query(
        college_label,
        func.count(func.distinct(Application.user_id))
    ).join(Application, Application.user_id == User.id) \
     .outerjoin(College, College.id == User.college_id) \
     .filter(Application.status == 'approved') \
     .group_by(college_label) \
     .order_by(func.count(func.distinct(Application.user_id)).desc()).all()

    return {
        'colleges': [r[0] for r in results],
        'counts': [r[1] for r in results],
    }


def get_monthly_hours_trend():
    """每月服务时长趋势（折线图）"""
    results = db.session.query(
        extract('year', Checkin.sign_in_time).label('year'),
        extract('month', Checkin.sign_in_time).label('month'),
        func.sum(Checkin.duration_hours),
    ).filter(
        Checkin.status == 'confirmed',
        Checkin.sign_in_time.isnot(None),
    ).group_by('year', 'month').order_by('year', 'month').all()

    return {
        'months': [f'{int(r[0])}-{int(r[1]):02d}' for r in results],
        'hours': [round(r[2] or 0, 2) for r in results],
    }


def get_project_application_stats():
    """各项目报名人数对比（柱状图，取前15个）"""
    results = db.session.query(
        Project.title, func.count(Application.id)
    ).join(Application, Application.project_id == Project.id).filter(
        Project.is_deleted == False,
        Application.status != 'cancelled',
    ).group_by(Project.id).order_by(func.count(Application.id).desc()).limit(15).all()

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
        # 管理员：复用总览数据
        stats = get_overview_stats()
        return {
            'cards': [
                {'title': '项目总数', 'value': stats['projectCount'], 'unit': '个', 'color': 'blue'},
                {'title': '志愿者人数', 'value': stats['volunteerCount'], 'unit': '人', 'color': 'green'},
                {'title': '累计总时长', 'value': stats['totalHours'], 'unit': '小时', 'color': 'orange'},
            ]
        }

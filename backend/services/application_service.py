from datetime import datetime
from models import db
from models.application import Application
from models.project import Project


def apply_project(user_id, project_id, reason=None):
    """学生报名项目"""
    project = Project.query.get(project_id)
    if not project or project.is_deleted:
        raise ValueError('项目不存在')
    if project.status != 'published':
        raise ValueError('该项目当前不可报名')

    # 报名截止时间校验
    if project.registration_deadline and datetime.now() > project.registration_deadline:
        raise ValueError('报名已截止')

    # 防止重复报名（排除已取消的）
    existing = Application.query.filter_by(
        project_id=project_id, user_id=user_id
    ).filter(Application.status != 'cancelled').first()
    if existing:
        raise ValueError('您已报名该项目，请勿重复报名')

    # 检查名额是否已满
    approved_count = get_approved_count(project_id)
    if project.max_people > 0 and approved_count >= project.max_people:
        raise ValueError('该项目名额已满')

    app = Application(
        project_id=project_id,
        user_id=user_id,
        apply_reason=reason,
        status='pending',
    )
    db.session.add(app)
    db.session.commit()
    return app


def cancel_application(app_id, user_id):
    """取消报名（仅 pending 状态、仅本人）"""
    app = _get_application_or_raise(app_id)
    if app.user_id != user_id:
        raise PermissionError('只能取消自己的报名')
    if app.status != 'pending':
        raise ValueError('只有待审核状态的报名可以取消')

    app.status = 'cancelled'
    db.session.commit()
    return app


def approve_application(app_id, leader_id):
    """通过报名（名额控制）"""
    app = _get_application_or_raise(app_id)
    project = app.project

    # 校验操作者是项目创建者
    if project.creator_id != leader_id:
        raise PermissionError('只能审核自己创建的项目的报名')
    if app.status != 'pending':
        raise ValueError('只有待审核状态的报名可以审批')

    # 名额校验
    approved_count = get_approved_count(app.project_id)
    if project.max_people > 0 and approved_count >= project.max_people:
        raise ValueError(f'名额已满（{approved_count}/{project.max_people}），无法继续通过')

    app.status = 'approved'
    app.review_time = datetime.now()
    db.session.commit()
    return app


def reject_application(app_id, leader_id, remark=None):
    """拒绝报名"""
    app = _get_application_or_raise(app_id)
    project = app.project

    if project.creator_id != leader_id:
        raise PermissionError('只能审核自己创建的项目的报名')
    if app.status != 'pending':
        raise ValueError('只有待审核状态的报名可以审批')

    app.status = 'rejected'
    app.review_time = datetime.now()
    app.review_remark = remark
    db.session.commit()
    return app


def get_project_applications(project_id, status=None, page=1, page_size=10):
    """获取某项目的报名列表"""
    query = Application.query.filter_by(project_id=project_id)
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Application.apply_time.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return {
        'list': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size,
    }


def get_my_applications(user_id, status=None, page=1, page_size=10):
    """获取我的报名记录"""
    query = Application.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Application.apply_time.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return {
        'list': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size,
    }


def get_application_status(project_id, user_id):
    """查询某用户在某项目的报名状态"""
    app = Application.query.filter_by(
        project_id=project_id, user_id=user_id
    ).filter(Application.status != 'cancelled').first()
    if not app:
        return None
    return app.to_dict()


def get_approved_count(project_id):
    """查询已通过人数"""
    return Application.query.filter_by(
        project_id=project_id, status='approved'
    ).count()


def _get_application_or_raise(app_id):
    """获取报名记录，不存在则抛异常"""
    app = Application.query.get(app_id)
    if not app:
        raise ValueError('报名记录不存在')
    return app

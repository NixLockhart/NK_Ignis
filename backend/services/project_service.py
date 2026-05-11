from datetime import datetime
from models import db
from models.project import Project


def create_project(creator_id, data):
    """创建项目（默认草稿状态）"""
    project = Project(
        title=data['title'],
        content=data.get('content', ''),
        location=data.get('location', ''),
        category=data.get('category', ''),
        start_time=_parse_time(data.get('startTime')),
        end_time=_parse_time(data.get('endTime')),
        registration_deadline=_parse_time(data.get('registrationDeadline')),
        max_people=int(data.get('maxPeople', 0)),
        contact=data.get('contact', ''),
        notice=data.get('notice', ''),
        lat=_parse_float(data.get('lat')),
        lng=_parse_float(data.get('lng')),
        radius_m=int(data.get('radiusM') or 200),
        sign_in_window_minutes=int(data.get('signInWindowMinutes') or 30),
        status='draft',
        creator_id=creator_id,
    )
    db.session.add(project)
    db.session.commit()
    return project


def update_project(project_id, user_id, data):
    """编辑项目（仅草稿状态、仅创建者）"""
    project = _get_project_or_raise(project_id)
    if project.creator_id != user_id:
        raise PermissionError('只能编辑自己创建的项目')
    if project.status != 'draft':
        raise ValueError('只有草稿状态的项目可以编辑')

    updatable = ['title', 'content', 'location', 'category', 'contact', 'notice']
    for field in updatable:
        if field in data:
            setattr(project, field, data[field])

    # 驼峰字段特殊处理
    if 'startTime' in data:
        project.start_time = _parse_time(data['startTime'])
    if 'endTime' in data:
        project.end_time = _parse_time(data['endTime'])
    if 'registrationDeadline' in data:
        project.registration_deadline = _parse_time(data['registrationDeadline'])
    if 'maxPeople' in data:
        project.max_people = int(data['maxPeople'])

    # 打卡真实性相关字段（P1-11）
    if 'lat' in data:
        project.lat = _parse_float(data['lat'])
    if 'lng' in data:
        project.lng = _parse_float(data['lng'])
    if 'radiusM' in data:
        project.radius_m = int(data['radiusM'] or 200)
    if 'signInWindowMinutes' in data:
        project.sign_in_window_minutes = int(data['signInWindowMinutes'] or 30)

    db.session.commit()
    return project


def delete_project(project_id, user_id):
    """逻辑删除项目（仅草稿状态、仅创建者）"""
    project = _get_project_or_raise(project_id)
    if project.creator_id != user_id:
        raise PermissionError('只能删除自己创建的项目')
    if project.status != 'draft':
        raise ValueError('只有草稿状态的项目可以删除')

    project.is_deleted = True
    db.session.commit()


def submit_for_review(project_id, user_id):
    """提交审核 draft → pending"""
    project = _get_project_or_raise(project_id)
    if project.creator_id != user_id:
        raise PermissionError('只能提交自己创建的项目')
    if not project.can_transition_to('pending'):
        raise ValueError(f'当前状态 [{project.STATUS_LABELS.get(project.status)}] 不能提交审核')

    # 基本完整性校验
    if not project.title or not project.start_time or not project.end_time or project.max_people <= 0:
        raise ValueError('项目信息不完整，请填写名称、时间和招募人数')

    project.status = 'pending'
    project.review_remark = None
    db.session.commit()
    return project


def approve_project(project_id, remark=None):
    """审核通过 pending → published"""
    project = _get_project_or_raise(project_id)
    if not project.can_transition_to('published'):
        raise ValueError(f'当前状态 [{project.STATUS_LABELS.get(project.status)}] 不能审核通过')

    project.status = 'published'
    project.review_remark = remark
    db.session.commit()
    return project


def reject_project(project_id, remark=None):
    """审核驳回 pending → draft"""
    project = _get_project_or_raise(project_id)
    if not project.can_transition_to('draft'):
        raise ValueError(f'当前状态 [{project.STATUS_LABELS.get(project.status)}] 不能驳回')
    if project.status != 'pending':
        raise ValueError('只有待审核状态的项目可以驳回')

    project.status = 'draft'
    project.review_remark = remark
    db.session.commit()
    return project


def get_project_list(status=None, category=None, page=1, page_size=10, published_only=False):
    """获取项目列表（分页、筛选）"""
    # 懒检测：自动流转过期项目状态
    _auto_transition_projects()

    query = Project.query.filter_by(is_deleted=False)

    if published_only:
        # 学生视角：只看已发布及之后的状态
        query = query.filter(Project.status.in_(['published', 'registration_closed', 'in_progress', 'completed']))
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)

    query = query.order_by(Project.created_at.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return {
        'list': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size,
    }


def get_my_projects(user_id, status=None, page=1, page_size=10):
    """获取我创建的项目列表"""
    query = Project.query.filter_by(creator_id=user_id, is_deleted=False)
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Project.created_at.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return {
        'list': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size,
    }


def get_project_detail(project_id):
    """获取项目详情"""
    project = _get_project_or_raise(project_id)
    return project.to_dict()


def _get_project_or_raise(project_id):
    """获取项目，不存在或已删除则抛异常"""
    project = Project.query.get(project_id)
    if not project or project.is_deleted:
        raise ValueError('项目不存在')
    return project


def _parse_time(time_str):
    """解析时间字符串"""
    if not time_str:
        return None
    try:
        return datetime.fromisoformat(time_str)
    except (ValueError, TypeError):
        return None


def _parse_float(v):
    """解析浮点数（None / 空字符串返回 None）"""
    if v is None or v == '':
        return None
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _auto_transition_projects():
    """自动流转过期项目状态（懒检测）"""
    now = datetime.now()
    changed = False

    # 已发布且报名截止时间已过 → registration_closed
    expired_reg = Project.query.filter(
        Project.status == 'published',
        Project.is_deleted == False,
        Project.registration_deadline.isnot(None),
        Project.registration_deadline < now,
    ).all()
    for p in expired_reg:
        p.status = 'registration_closed'
        changed = True

    # registration_closed 且活动开始时间已过 → in_progress
    started = Project.query.filter(
        Project.status == 'registration_closed',
        Project.is_deleted == False,
        Project.start_time.isnot(None),
        Project.start_time < now,
    ).all()
    for p in started:
        p.status = 'in_progress'
        changed = True

    # in_progress 且活动结束时间已过 → completed
    ended = Project.query.filter(
        Project.status == 'in_progress',
        Project.is_deleted == False,
        Project.end_time.isnot(None),
        Project.end_time < now,
    ).all()
    for p in ended:
        p.status = 'completed'
        changed = True

    if changed:
        db.session.commit()

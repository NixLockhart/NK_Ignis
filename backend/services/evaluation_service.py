from models import db
from models.evaluation import Evaluation
from models.checkin import Checkin
from models.project import Project


def create_evaluation(user_id, project_id, score, content=None):
    """学生评价活动"""
    project = Project.query.get(project_id)
    if not project or project.is_deleted:
        raise ValueError('项目不存在')

    # 校验是否已签退（参与过活动）
    checkin = Checkin.query.filter_by(
        project_id=project_id, user_id=user_id
    ).filter(Checkin.sign_out_time.isnot(None)).first()
    if not checkin:
        raise ValueError('您尚未完成该项目的签到签退，无法评价')

    # 校验是否已评价
    existing = Evaluation.query.filter_by(
        project_id=project_id, user_id=user_id, evaluator_role='student'
    ).first()
    if existing:
        raise ValueError('您已评价过该项目')

    # 校验分数
    if not isinstance(score, int) or score < 1 or score > 5:
        raise ValueError('评分必须为1-5的整数')

    evaluation = Evaluation(
        project_id=project_id,
        user_id=user_id,
        evaluator_role='student',
        score=score,
        content=content,
    )
    db.session.add(evaluation)
    db.session.commit()
    return evaluation


def create_leader_comment(leader_id, project_id, target_user_id, score, content=None):
    """负责人评价学生"""
    project = Project.query.get(project_id)
    if not project or project.is_deleted:
        raise ValueError('项目不存在')
    if project.creator_id != leader_id:
        raise PermissionError('只能评价自己创建的项目的参与者')

    if not isinstance(score, int) or score < 1 or score > 5:
        raise ValueError('评分必须为1-5的整数')

    # 校验是否已评价该学生
    existing = Evaluation.query.filter_by(
        project_id=project_id, user_id=leader_id,
        evaluator_role='leader', target_user_id=target_user_id
    ).first()
    if existing:
        raise ValueError('已评价过该学生')

    evaluation = Evaluation(
        project_id=project_id,
        user_id=leader_id,
        evaluator_role='leader',
        target_user_id=target_user_id,
        score=score,
        content=content,
    )
    db.session.add(evaluation)
    db.session.commit()
    return evaluation


def get_project_evaluations(project_id, page=1, page_size=10):
    """某项目的评价列表"""
    query = Evaluation.query.filter_by(project_id=project_id)
    query = query.order_by(Evaluation.created_at.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return {
        'list': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size,
    }


def get_my_evaluations(user_id, page=1, page_size=10):
    """我的评价记录"""
    query = Evaluation.query.filter_by(user_id=user_id, evaluator_role='student')
    query = query.order_by(Evaluation.created_at.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return {
        'list': [e.to_dict() for e in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size,
    }

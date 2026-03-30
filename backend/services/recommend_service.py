import json
from sqlalchemy import func
from flask import current_app
from models import db
from models.user import User
from models.project import Project
from models.application import Application
from models.checkin import Checkin
from services.ai_service import _call_dify_api, _get_base_url


def get_recommendations(user_id):
    """基于规则的项目推荐（不依赖AI）"""
    user = User.query.get(user_id)
    if not user:
        return []

    # 1. 获取学生历史参与的项目类型分布
    history_categories = db.session.query(
        Project.category, func.count(Application.id)
    ).join(Application, Application.project_id == Project.id).filter(
        Application.user_id == user_id,
        Application.status == 'approved',
        Project.category.isnot(None),
        Project.category != '',
    ).group_by(Project.category).all()

    preferred_categories = [r[0] for r in sorted(history_categories, key=lambda x: x[1], reverse=True)]

    # 2. 获取当前可报名项目（已发布且学生未报名）
    already_applied = db.session.query(Application.project_id).filter(
        Application.user_id == user_id,
        Application.status != 'cancelled',
    ).subquery()

    candidates = Project.query.filter(
        Project.is_deleted == False,
        Project.status == 'published',
        ~Project.id.in_(already_applied),
    ).all()

    if not candidates:
        return []

    # 3. 打分排序
    scored = []
    for p in candidates:
        score = 0
        # 同类型项目优先
        if p.category in preferred_categories:
            idx = preferred_categories.index(p.category)
            score += max(10 - idx * 2, 1)
        # 同学院创建的项目加权
        if p.creator and p.creator.college == user.college:
            score += 3
        scored.append((p, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top_projects = [item[0] for item in scored[:8]]

    return [{
        'projectId': p.id,
        'title': p.title,
        'category': p.category,
        'location': p.location,
        'startTime': p.start_time.isoformat() if p.start_time else None,
        'endTime': p.end_time.isoformat() if p.end_time else None,
        'maxPeople': p.max_people,
        'creatorName': p.creator.real_name if p.creator else None,
        'reason': '',  # 无AI时无推荐理由
    } for p in top_projects]


def get_recommendations_with_ai(user_id):
    """规则推荐 + AI 生成推荐理由"""
    user = User.query.get(user_id)
    if not user:
        return []

    recommendations = get_recommendations(user_id)
    if not recommendations:
        return []

    # 获取历史参与类型
    history_categories = db.session.query(
        Project.category
    ).join(Application, Application.project_id == Project.id).filter(
        Application.user_id == user_id,
        Application.status == 'approved',
        Project.category.isnot(None),
    ).distinct().all()
    history_str = '、'.join([r[0] for r in history_categories]) or '暂无'

    # 尝试调用 Dify 生成推荐理由
    base_url = _get_base_url()
    api_key = current_app.config.get('DIFY_RECOMMEND_API_KEY', '')
    if not base_url or not api_key:
        # 未配置AI，使用默认推荐理由
        for rec in recommendations:
            rec['reason'] = _default_reason(rec, user, history_str)
        return recommendations

    # 构造项目列表摘要
    project_summary = json.dumps([{
        'project_id': r['projectId'],
        'title': r['title'],
        'category': r['category'] or '其他',
        'location': r['location'] or '',
    } for r in recommendations], ensure_ascii=False)

    payload = {
        'inputs': {
            'student_name': user.real_name,
            'student_college': user.college,
            'history_categories': history_str,
            'project_list': project_summary,
        },
        'response_mode': 'blocking',
        'user': str(user_id),
    }

    try:
        result = _call_dify_api(f'{base_url}/workflows/run', api_key, payload)
        outputs = result.get('data', {}).get('outputs', {})
        # 尝试解析AI返回的JSON
        ai_text = ''
        for v in outputs.values():
            if isinstance(v, str) and len(v) > 5:
                ai_text = v
                break

        if ai_text:
            # 尝试解析JSON数组
            ai_reasons = json.loads(ai_text)
            reason_map = {item['project_id']: item['reason'] for item in ai_reasons if 'project_id' in item}
            for rec in recommendations:
                rec['reason'] = reason_map.get(rec['projectId'], _default_reason(rec, user, history_str))
        else:
            for rec in recommendations:
                rec['reason'] = _default_reason(rec, user, history_str)
    except Exception:
        # AI调用失败，使用默认推荐理由
        for rec in recommendations:
            rec['reason'] = _default_reason(rec, user, history_str)

    return recommendations


def _default_reason(rec, user, history_str):
    """生成默认推荐理由（不依赖AI）"""
    category = rec.get('category') or '志愿服务'
    if history_str and history_str != '暂无' and category in history_str:
        return f'您曾参与过{category}类活动，推荐继续参与类似项目。'
    return f'该{category}项目正在招募志愿者，欢迎报名参加。'

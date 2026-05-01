from models.checkin import Checkin
from models.project import Project
from models.user import User


def get_certificate_data(user_id, project_id):
    """获取某项目的证书数据"""
    user = User.query.get(user_id)
    if not user:
        raise ValueError('用户不存在')

    project = Project.query.get(project_id)
    if not project:
        raise ValueError('项目不存在')

    # 查询已确认的打卡记录
    checkin = Checkin.query.filter_by(
        user_id=user_id, project_id=project_id, status='confirmed'
    ).first()
    if not checkin:
        raise ValueError('无已确认的服务记录，无法生成证书')

    return {
        'userName': user.real_name,
        'studentId': user.student_id,
        'college': user.college_name,
        'major': user.major,
        'projectTitle': project.title,
        'projectCategory': project.category,
        'durationHours': checkin.duration_hours,
        'startTime': project.start_time.strftime('%Y年%m月%d日') if project.start_time else '',
        'endTime': project.end_time.strftime('%Y年%m月%d日') if project.end_time else '',
        'signInTime': checkin.sign_in_time.strftime('%Y年%m月%d日') if checkin.sign_in_time else '',
        'signOutTime': checkin.sign_out_time.strftime('%Y年%m月%d日') if checkin.sign_out_time else '',
    }


def get_my_certificate_list(user_id):
    """获取可生成证书的项目列表（有已确认时长的项目）"""
    checkins = Checkin.query.filter_by(
        user_id=user_id, status='confirmed'
    ).all()

    result = []
    for c in checkins:
        if c.project:
            result.append({
                'projectId': c.project_id,
                'projectTitle': c.project.title,
                'durationHours': c.duration_hours,
                'signInTime': c.sign_in_time.isoformat() if c.sign_in_time else None,
            })
    return result


def get_eligible_users(project_id):
    """获取某项目可生成证书的所有学生用户ID（有已确认打卡记录）"""
    rows = Checkin.query.filter_by(project_id=project_id, status='confirmed').all()
    seen = set()
    user_ids = []
    for c in rows:
        if c.user_id not in seen:
            seen.add(c.user_id)
            user_ids.append(c.user_id)
    return user_ids

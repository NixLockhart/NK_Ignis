import re
from models import db
from models.user import User
from models.college import College


def register_user(username, password, real_name, student_id, college, major, phone):
    """注册新用户"""
    # 密码强度校验
    if not password or len(password) < 6 or len(password) > 20:
        raise ValueError('密码长度必须在6到20个字符之间')

    # 手机号格式校验
    if not re.match(r'^1[3-9]\d{9}$', phone or ''):
        raise ValueError('请输入正确的手机号')

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        raise ValueError('用户名已存在')

    # 检查学号是否已存在
    if User.query.filter_by(student_id=student_id).first():
        raise ValueError('该学号已注册')

    # 查找学院
    college_obj = College.query.filter_by(name=college).first()

    user = User(
        username=username,
        real_name=real_name,
        student_id=student_id,
        college_id=college_obj.id if college_obj else None,
        college=college,
        major=major,
        phone=phone,
        role='student',
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(username, password):
    """验证用户登录"""
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        raise ValueError('用户名或密码错误')
    return user


def update_profile(user_id, data):
    """更新个人信息（允许修改：姓名、学院、专业、手机号）"""
    user = User.query.get(user_id)
    if not user:
        raise ValueError('用户不存在')

    if 'realName' in data and data['realName'].strip():
        user.real_name = data['realName'].strip()
    if 'college' in data and data['college'].strip():
        college_name = data['college'].strip()
        college_obj = College.query.filter_by(name=college_name).first()
        user.college_id = college_obj.id if college_obj else None
        user.college = college_name
    if 'major' in data and data['major'].strip():
        user.major = data['major'].strip()
    if 'phone' in data and data['phone'].strip():
        if not re.match(r'^1[3-9]\d{9}$', data['phone']):
            raise ValueError('请输入正确的手机号')
        user.phone = data['phone'].strip()

    db.session.commit()
    return user


def get_user_list(page=1, page_size=20, role=None, keyword=None):
    """管理员获取用户列表"""
    query = User.query
    if role:
        query = query.filter_by(role=role)
    if keyword:
        query = query.filter(
            db.or_(
                User.username.contains(keyword),
                User.real_name.contains(keyword),
                User.student_id.contains(keyword),
            )
        )
    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return {
        'list': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size,
    }


def update_user_role(user_id, new_role):
    """管理员修改用户角色"""
    if new_role not in ('student', 'leader', 'admin'):
        raise ValueError('无效的角色类型')

    user = User.query.get(user_id)
    if not user:
        raise ValueError('用户不存在')
    if user.username == 'admin':
        raise ValueError('不能修改超级管理员的角色')

    user.role = new_role
    db.session.commit()
    return user


def change_password(user_id, old_password, new_password):
    """用户自助修改密码"""
    user = User.query.get(user_id)
    if not user:
        raise ValueError('用户不存在')
    if not old_password or not user.check_password(old_password):
        raise ValueError('原密码错误')
    if not new_password or len(new_password) < 6 or len(new_password) > 20:
        raise ValueError('新密码长度必须在6到20个字符之间')
    if old_password == new_password:
        raise ValueError('新密码不能与原密码相同')

    user.set_password(new_password)
    db.session.commit()
    return user


def reset_password_by_admin(operator_id, target_user_id, new_password='123456'):
    """管理员重置用户密码（默认重置为 123456）"""
    operator = User.query.get(operator_id)
    if not operator or operator.role != 'admin':
        raise PermissionError('仅管理员可重置密码')

    target = User.query.get(target_user_id)
    if not target:
        raise ValueError('用户不存在')
    if target.username == 'admin':
        raise ValueError('不能重置超级管理员的密码')
    if not new_password or len(new_password) < 6 or len(new_password) > 20:
        raise ValueError('密码长度必须在6到20个字符之间')

    target.set_password(new_password)
    db.session.commit()
    return target

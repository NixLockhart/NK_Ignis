from flask import Blueprint, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from services.auth_service import (
    register_user, authenticate_user, update_profile,
    get_user_list, update_user_role,
)
from utils.response import success, error
from utils.log_util import log_operation
from utils.auth import require_current_user
from models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    if not data:
        return error('请求数据不能为空')

    required_fields = ['username', 'password', 'realName', 'studentId', 'college', 'major', 'phone']
    for field in required_fields:
        if not data.get(field):
            return error(f'缺少必填字段：{field}')

    try:
        user = register_user(
            username=data['username'],
            password=data['password'],
            real_name=data['realName'],
            student_id=data['studentId'],
            college=data['college'],
            major=data['major'],
            phone=data['phone'],
        )
        log_operation(user.id, 'register', 'user', user.id, f'用户 {user.username} 注册成功')
        return success(message='注册成功')
    except ValueError as e:
        return error(str(e))


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return error('请输入用户名和密码')

    try:
        user = authenticate_user(data['username'], data['password'])
        # 签发 JWT，identity 存储用户ID
        token = create_access_token(identity=str(user.id))
        log_operation(user.id, 'login', 'user', user.id, f'用户 {user.username} 登录成功')
        return success(data={'token': token}, message='登录成功')
    except ValueError as e:
        return error(str(e), 401)


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """获取当前用户信息"""
    user = require_current_user()
    return success(data=user.to_dict())


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile_route():
    """更新个人信息"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data:
        return error('请求数据不能为空')

    try:
        user = update_profile(user_id, data)
        log_operation(user_id, 'update_profile', 'user', user_id, '更新个人信息')
        return success(data=user.to_dict(), message='信息更新成功')
    except ValueError as e:
        return error(str(e))


@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def user_list():
    """管理员查看用户列表"""
    user = require_current_user()
    if user.role != 'admin':
        return error('仅管理员可查看用户列表', 403)

    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    role = request.args.get('role', None)
    keyword = request.args.get('keyword', None)

    result = get_user_list(page=page, page_size=page_size, role=role, keyword=keyword)
    return success(data=result)


@auth_bp.route('/role', methods=['PUT'])
@jwt_required()
def change_role():
    """管理员修改用户角色"""
    admin = require_current_user()
    if admin.role != 'admin':
        return error('仅管理员可修改角色', 403)

    data = request.get_json() or {}
    target_user_id = data.get('userId')
    new_role = (data.get('role') or '').strip()
    if not target_user_id or not new_role:
        return error('缺少用户ID或角色参数')

    try:
        user = update_user_role(target_user_id, new_role)
        log_operation(admin.id, 'change_role', 'user', target_user_id,
                      f'将用户 {user.username} 角色修改为 {new_role}')
        return success(message='角色修改成功')
    except ValueError as e:
        return error(str(e))

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.college import College
from models.user import User
from utils.response import success, error

college_bp = Blueprint('college', __name__, url_prefix='/api/college')


@college_bp.route('/list', methods=['GET'])
def college_list():
    """获取学院列表（公开接口，注册页也需要）"""
    colleges = College.query.order_by(College.sort_order, College.id).all()
    return success(data=[c.to_dict() for c in colleges])


@college_bp.route('', methods=['POST'])
@jwt_required()
def create_college():
    """新增学院（仅管理员）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if user.role != 'admin':
        return error('仅管理员可操作', 403)

    data = request.get_json()
    name = (data.get('name') or '').strip()
    if not name:
        return error('学院名称不能为空')
    if College.query.filter_by(name=name).first():
        return error('该学院已存在')

    c = College(name=name, sort_order=data.get('sortOrder', 0))
    db.session.add(c)
    db.session.commit()
    return success(data=c.to_dict(), message='添加成功')


@college_bp.route('/<int:college_id>', methods=['PUT'])
@jwt_required()
def update_college(college_id):
    """修改学院（仅管理员）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if user.role != 'admin':
        return error('仅管理员可操作', 403)

    c = College.query.get(college_id)
    if not c:
        return error('学院不存在', 404)

    data = request.get_json()
    name = (data.get('name') or '').strip()
    if name and name != c.name:
        if College.query.filter_by(name=name).first():
            return error('该学院名称已存在')
        c.name = name
    if 'sortOrder' in data:
        c.sort_order = data['sortOrder']

    db.session.commit()
    return success(data=c.to_dict(), message='修改成功')


@college_bp.route('/<int:college_id>', methods=['DELETE'])
@jwt_required()
def delete_college(college_id):
    """删除学院（仅管理员）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if user.role != 'admin':
        return error('仅管理员可操作', 403)

    c = College.query.get(college_id)
    if not c:
        return error('学院不存在', 404)

    db.session.delete(c)
    db.session.commit()
    return success(message='删除成功')

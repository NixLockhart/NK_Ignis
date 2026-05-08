"""统一的当前登录用户解析工具

所有 routes 应通过 require_current_user() 获取当前用户，替代各文件本地的
_get_current_user()。当 token 有效但 user 已被删除时，require_current_user
会触发 abort(401)，配合 app.py 注册的全局 HTTPException 处理器返回项目统一
JSON 格式，避免 None.role 类型的 AttributeError 500。
"""
from flask import abort
from flask_jwt_extended import get_jwt_identity

from models.user import User


def get_current_user_or_none():
    """获取当前登录用户对象；token 无效或 user 已被删除时返回 None。"""
    raw = get_jwt_identity()
    if raw is None:
        return None
    try:
        user_id = int(raw)
    except (TypeError, ValueError):
        return None
    return User.query.get(user_id)


def require_current_user():
    """获取当前登录用户对象；不存在时直接 abort(401)。

    各 routes 文件可用 `from utils.auth import require_current_user as _get_current_user`
    替换本地实现，调用点代码无需任何改动。
    """
    user = get_current_user_or_none()
    if user is None:
        abort(401, description='用户不存在或已被删除')
    return user

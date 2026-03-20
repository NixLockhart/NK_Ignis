from flask import jsonify


def success(data=None, message='操作成功'):
    """统一成功响应"""
    return jsonify({'code': 200, 'message': message, 'data': data})


def error(message='操作失败', code=400):
    """统一错误响应"""
    return jsonify({'code': code, 'message': message, 'data': None}), code

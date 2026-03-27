from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import certificate_service
from utils.response import success, error
from utils.log_util import log_operation

certificate_bp = Blueprint('certificate', __name__, url_prefix='/api/certificate')


@certificate_bp.route('/data', methods=['GET'])
@jwt_required()
def certificate_data():
    """获取证书数据"""
    user_id = int(get_jwt_identity())
    project_id = request.args.get('projectId', type=int)
    if not project_id:
        return error('缺少项目ID')

    try:
        data = certificate_service.get_certificate_data(user_id, project_id)
        log_operation(user_id, 'generate_certificate', 'project', project_id,
                      f'查看证书：{data["projectTitle"]}')
        return success(data=data)
    except ValueError as e:
        return error(str(e))


@certificate_bp.route('/my-list', methods=['GET'])
@jwt_required()
def my_certificate_list():
    """可获得证书的项目列表"""
    user_id = int(get_jwt_identity())
    data = certificate_service.get_my_certificate_list(user_id)
    return success(data=data)

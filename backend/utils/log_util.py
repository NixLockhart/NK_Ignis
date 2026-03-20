from flask import request as flask_request
from models import db
from models.operation_log import OperationLog


def log_operation(user_id, action, target_type=None, target_id=None, detail=None):
    """记录操作日志"""
    ip_address = flask_request.remote_addr if flask_request else None
    log = OperationLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.session.add(log)
    db.session.commit()

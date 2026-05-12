import logging

from flask import request as flask_request
from models import db
from models.operation_log import OperationLog


def log_operation(user_id, action, target_type=None, target_id=None, detail=None):
    """记录操作日志。

    日志写入失败不会拖累主业务流程 —— 失败时回滚并写一条 warning，
    主业务函数返回的成功/失败状态保持不变。
    """
    try:
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
    except Exception as e:
        db.session.rollback()
        logging.warning('log_operation failed (action=%s, user_id=%s): %s',
                        action, user_id, e)

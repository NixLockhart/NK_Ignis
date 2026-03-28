from datetime import datetime
from models import db
from models.operation_log import OperationLog


def get_logs(action=None, user_id=None, start_date=None, end_date=None, page=1, page_size=20):
    """分页查询操作日志"""
    query = OperationLog.query

    if action:
        query = query.filter_by(action=action)
    if user_id:
        query = query.filter_by(user_id=user_id)
    if start_date:
        query = query.filter(OperationLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(OperationLog.created_at <= datetime.fromisoformat(end_date))

    query = query.order_by(OperationLog.created_at.desc())
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return {
        'list': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'page': page,
        'pageSize': page_size,
    }

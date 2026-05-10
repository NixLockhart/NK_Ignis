from datetime import datetime
from models import db


class OperationLog(db.Model):
    """操作日志表"""
    __tablename__ = 'tb_operation_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'), comment='操作人ID')
    action = db.Column(db.String(50), nullable=False, comment='操作类型')
    target_type = db.Column(db.String(50), comment='操作对象类型')
    target_id = db.Column(db.Integer, comment='操作对象ID')
    detail = db.Column(db.String(500), comment='操作描述')
    ip_address = db.Column(db.String(50), comment='IP地址')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    user = db.relationship('User', backref='operation_logs', lazy=True)

    # 操作类型中文映射
    ACTION_LABELS = {
        'register': '用户注册', 'login': '用户登录',
        'create_project': '创建项目', 'update_project': '编辑项目',
        'delete_project': '删除项目', 'submit_project': '提交审核',
        'approve_project': '审核通过', 'reject_project': '审核驳回',
        'apply_project': '报名项目', 'cancel_application': '取消报名',
        'approve_application': '通过报名', 'reject_application': '拒绝报名',
        'sign_in': '签到', 'sign_out': '签退',
        'confirm_checkin': '确认打卡', 'reject_checkin': '驳回打卡',
        'create_evaluation': '评价活动', 'leader_comment': '负责人评价',
        'export_applications': '导出报名', 'export_project_stats': '导出项目统计',
        'export_hours_records': '导出时长', 'generate_certificate': '生成证书',
        'ai_policy_qa': 'AI政策问答', 'ai_certificate_text': 'AI文案生成',
        'ai_nl_query': 'AI数据查询', 'ai_recommend': 'AI项目推荐',
        'update_profile': '更新个人信息', 'change_role': '修改用户角色',
        'change_password': '修改密码', 'reset_password': '重置密码',
    }

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'userName': self.user.real_name if self.user else None,
            'action': self.action,
            'actionLabel': self.ACTION_LABELS.get(self.action, self.action),
            'targetType': self.target_type,
            'targetId': self.target_id,
            'detail': self.detail,
            'ipAddress': self.ip_address,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }

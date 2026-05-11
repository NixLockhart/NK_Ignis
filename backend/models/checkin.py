from datetime import datetime
from models import db


class Checkin(db.Model):
    """签到/签退打卡记录表"""
    __tablename__ = 'tb_checkin'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('tb_project.id'), nullable=False,
                           comment='项目ID')
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'), nullable=False,
                        comment='打卡人ID')
    sign_in_time = db.Column(db.DateTime, comment='签到时间')
    sign_out_time = db.Column(db.DateTime, comment='签退时间')
    duration_hours = db.Column(db.Float, comment='服务时长（小时）')
    status = db.Column(db.String(20), nullable=False, default='pending',
                       comment='状态：pending/confirmed/rejected')
    is_abnormal = db.Column(db.Boolean, default=False, comment='异常标记')
    abnormal_reason = db.Column(db.String(100), comment='异常原因分类：time_window/location/duration_too_short/duration_too_long')
    remark = db.Column(db.String(500), comment='备注/驳回原因')
    checked_by = db.Column(db.Integer, db.ForeignKey('tb_user.id'), comment='确认人ID')
    checked_time = db.Column(db.DateTime, comment='确认时间')

    STATUS_LABELS = {
        'pending': '待确认',
        'confirmed': '已确认',
        'rejected': '已驳回',
    }

    ABNORMAL_REASON_LABELS = {
        'time_window': '签到时间异常',
        'location': '签到位置异常',
        'duration_too_short': '服务时长过短',
        'duration_too_long': '服务时长异常长',
    }

    project = db.relationship('Project', backref='checkins', lazy=True)
    user = db.relationship('User', foreign_keys=[user_id], backref='checkins', lazy=True)
    checker = db.relationship('User', foreign_keys=[checked_by], lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'projectId': self.project_id,
            'projectTitle': self.project.title if self.project else None,
            'userId': self.user_id,
            'userName': self.user.real_name if self.user else None,
            'userStudentId': self.user.student_id if self.user else None,
            'signInTime': self.sign_in_time.isoformat() if self.sign_in_time else None,
            'signOutTime': self.sign_out_time.isoformat() if self.sign_out_time else None,
            'durationHours': self.duration_hours,
            'status': self.status,
            'statusLabel': self.STATUS_LABELS.get(self.status, '未知'),
            'isAbnormal': self.is_abnormal,
            'abnormalReason': self.abnormal_reason,
            'abnormalReasonLabel': self.ABNORMAL_REASON_LABELS.get(self.abnormal_reason, '') if self.abnormal_reason else None,
            'remark': self.remark,
            'checkedBy': self.checked_by,
            'checkerName': self.checker.real_name if self.checker else None,
            'checkedTime': self.checked_time.isoformat() if self.checked_time else None,
        }

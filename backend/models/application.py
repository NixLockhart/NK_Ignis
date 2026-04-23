from datetime import datetime
from models import db


class Application(db.Model):
    """报名记录表"""
    __tablename__ = 'tb_application'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('tb_project.id'), nullable=False,
                           comment='项目ID')
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'), nullable=False,
                        comment='报名人ID')
    apply_reason = db.Column(db.String(500), comment='报名说明')
    status = db.Column(db.String(20), nullable=False, default='pending',
                       comment='状态：pending/approved/rejected/cancelled')
    apply_time = db.Column(db.DateTime, default=datetime.now, comment='报名时间')
    review_time = db.Column(db.DateTime, comment='审核时间')
    review_remark = db.Column(db.String(500), comment='审核意见')

    # 状态中文映射
    STATUS_LABELS = {
        'pending': '待审核',
        'approved': '已通过',
        'rejected': '已拒绝',
        'cancelled': '已取消',
    }

    project = db.relationship('Project', backref='applications', lazy=True)
    user = db.relationship('User', backref='applications', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'projectId': self.project_id,
            'projectTitle': self.project.title if self.project else None,
            'userId': self.user_id,
            'userName': self.user.real_name if self.user else None,
            'userStudentId': self.user.student_id if self.user else None,
            'userCollege': self.user.college_name if self.user else None,
            'applyReason': self.apply_reason,
            'status': self.status,
            'statusLabel': self.STATUS_LABELS.get(self.status, '未知'),
            'applyTime': self.apply_time.isoformat() if self.apply_time else None,
            'reviewTime': self.review_time.isoformat() if self.review_time else None,
            'reviewRemark': self.review_remark,
        }

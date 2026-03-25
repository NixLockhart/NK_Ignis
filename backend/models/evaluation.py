from datetime import datetime
from models import db


class Evaluation(db.Model):
    """活动评价表"""
    __tablename__ = 'tb_evaluation'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('tb_project.id'), nullable=False,
                           comment='项目ID')
    user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'), nullable=False,
                        comment='评价人ID')
    evaluator_role = db.Column(db.String(20), nullable=False,
                               comment='评价者角色：student/leader')
    target_user_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'),
                               comment='被评学生ID（负责人评学生时使用）')
    score = db.Column(db.Integer, nullable=False, comment='评分1-5')
    content = db.Column(db.Text, comment='评价内容')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    project = db.relationship('Project', backref='evaluations', lazy=True)
    user = db.relationship('User', foreign_keys=[user_id], backref='evaluations_given', lazy=True)
    target_user = db.relationship('User', foreign_keys=[target_user_id], lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'projectId': self.project_id,
            'projectTitle': self.project.title if self.project else None,
            'userId': self.user_id,
            'userName': self.user.real_name if self.user else None,
            'evaluatorRole': self.evaluator_role,
            'targetUserId': self.target_user_id,
            'targetUserName': self.target_user.real_name if self.target_user else None,
            'score': self.score,
            'content': self.content,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }

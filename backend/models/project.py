from datetime import datetime
from models import db


class Project(db.Model):
    """志愿项目表"""
    __tablename__ = 'tb_project'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, comment='项目名称')
    content = db.Column(db.Text, comment='活动简介')
    location = db.Column(db.String(200), comment='活动地点')
    category = db.Column(db.String(50), comment='活动类型')
    start_time = db.Column(db.DateTime, comment='开始时间')
    end_time = db.Column(db.DateTime, comment='结束时间')
    registration_deadline = db.Column(db.DateTime, comment='报名截止时间')
    max_people = db.Column(db.Integer, default=0, comment='招募人数')
    status = db.Column(db.String(30), nullable=False, default='draft',
                       comment='状态：draft/pending/published/registration_closed/in_progress/completed')
    contact = db.Column(db.String(100), comment='联系方式')
    notice = db.Column(db.Text, comment='注意事项')
    review_remark = db.Column(db.String(500), comment='审核意见')
    is_deleted = db.Column(db.Boolean, default=False, comment='逻辑删除标记')
    creator_id = db.Column(db.Integer, db.ForeignKey('tb_user.id'), nullable=False,
                           comment='创建人ID')

    # ====== 打卡真实性控制（P1-11 三重验证：时间窗 + 地理位置 + 负责人确认）======
    lat = db.Column(db.Float, nullable=True, comment='签到地点纬度（不填则不做位置校验）')
    lng = db.Column(db.Float, nullable=True, comment='签到地点经度（不填则不做位置校验）')
    radius_m = db.Column(db.Integer, default=200, comment='签到允许半径（米）')
    sign_in_window_minutes = db.Column(db.Integer, default=30,
                                       comment='允许提前/延后签到的分钟数')

    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,
                           comment='更新时间')

    creator = db.relationship('User', backref='projects', lazy=True)

    # 状态流转规则
    VALID_TRANSITIONS = {
        'draft': ['pending'],
        'pending': ['published', 'draft'],
        'published': ['registration_closed'],
        'registration_closed': ['in_progress'],
        'in_progress': ['completed'],
        'completed': [],
    }

    # 状态中文映射
    STATUS_LABELS = {
        'draft': '草稿',
        'pending': '待审核',
        'published': '已发布',
        'registration_closed': '报名结束',
        'in_progress': '进行中',
        'completed': '已结束',
    }

    def can_transition_to(self, new_status):
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'location': self.location,
            'category': self.category,
            'startTime': self.start_time.isoformat() if self.start_time else None,
            'endTime': self.end_time.isoformat() if self.end_time else None,
            'registrationDeadline': self.registration_deadline.isoformat() if self.registration_deadline else None,
            'maxPeople': self.max_people,
            'status': self.status,
            'statusLabel': self.STATUS_LABELS.get(self.status, '未知'),
            'contact': self.contact,
            'notice': self.notice,
            'reviewRemark': self.review_remark,
            'lat': self.lat,
            'lng': self.lng,
            'radiusM': self.radius_m,
            'signInWindowMinutes': self.sign_in_window_minutes,
            'creatorId': self.creator_id,
            'creatorName': self.creator.real_name if self.creator else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }

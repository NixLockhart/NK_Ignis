from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from models import db


class User(db.Model):
    """用户表"""
    __tablename__ = 'tb_user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password_hash = db.Column(db.String(256), nullable=False, comment='密码哈希')
    real_name = db.Column(db.String(50), nullable=False, comment='真实姓名')
    student_id = db.Column(db.String(20), unique=True, nullable=False, comment='学号')
    college_id = db.Column(db.Integer, db.ForeignKey('tb_college.id'), comment='学院ID')
    college = db.Column(db.String(100), comment='学院（兼容旧数据）')
    major = db.Column(db.String(100), nullable=False, comment='专业')
    role = db.Column(db.String(20), nullable=False, default='student',
                     comment='角色：student/leader/admin')
    phone = db.Column(db.String(20), nullable=False, comment='手机号')
    email = db.Column(db.String(100), nullable=True, comment='邮箱（可选）')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,
                           comment='更新时间')

    college_ref = db.relationship('College', backref='users', lazy=True, foreign_keys=[college_id])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def college_name(self):
        """优先从外键关联取学院名，兼容旧字符串字段"""
        if self.college_ref:
            return self.college_ref.name
        return self.college or ''

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'realName': self.real_name,
            'studentId': self.student_id,
            'college': self.college_name,
            'collegeId': self.college_id,
            'major': self.major,
            'role': self.role,
            'phone': self.phone,
            'email': self.email,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }

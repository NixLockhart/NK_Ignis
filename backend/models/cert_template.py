from datetime import datetime
from models import db


class CertTemplate(db.Model):
    """证书模板表"""
    __tablename__ = 'tb_cert_template'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True, comment='模板名称')
    bg_color = db.Column(db.String(20), nullable=False, default='#F8FAFB', comment='背景色')
    accent_color = db.Column(db.String(20), nullable=False, default='#4F6EF7', comment='装饰色')
    signature_text = db.Column(db.String(100), nullable=False,
                               default='高校青年志愿者服务中心', comment='签发单位文本')
    commendation_style = db.Column(db.String(20), nullable=False, default='formal',
                                   comment='表彰语风格：formal/warm/concise')
    is_default = db.Column(db.Boolean, default=False, comment='是否默认模板')
    enabled = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,
                           comment='更新时间')

    STYLE_LABELS = {
        'formal': '正式',
        'warm': '温情',
        'concise': '简洁',
    }

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'bgColor': self.bg_color,
            'accentColor': self.accent_color,
            'signatureText': self.signature_text,
            'commendationStyle': self.commendation_style,
            'commendationStyleLabel': self.STYLE_LABELS.get(self.commendation_style, ''),
            'isDefault': self.is_default,
            'enabled': self.enabled,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
        }

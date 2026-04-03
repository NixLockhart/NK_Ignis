from models import db


class College(db.Model):
    """学院表"""
    __tablename__ = 'tb_college'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True, comment='学院名称')
    sort_order = db.Column(db.Integer, default=0, comment='排序序号')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sortOrder': self.sort_order,
        }

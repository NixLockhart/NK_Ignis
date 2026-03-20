import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from routes import register_blueprints
from utils.response import success


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 初始化扩展
    db.init_app(app)
    JWTManager(app)
    CORS(app)

    # 注册蓝图
    register_blueprints(app)

    # 测试接口
    @app.route('/api/ping')
    def ping():
        return success(message='pong')

    # 创建数据库表 & 种子数据
    with app.app_context():
        # 导入所有模型以确保建表
        from models.user import User
        from models.project import Project
        from models.operation_log import OperationLog  # noqa: F841
        from models.application import Application  # noqa: F841
        from models.checkin import Checkin  # noqa: F841
        from models.evaluation import Evaluation  # noqa: F841

        db.create_all()
        _seed_admin(User)

    return app


def _seed_admin(User):
    """初始化管理员账号（仅在不存在时创建）"""
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            real_name='系统管理员',
            student_id='000000',
            college='管理部门',
            major='系统管理',
            phone='00000000000',
            role='admin',
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

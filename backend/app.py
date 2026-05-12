import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.exceptions import HTTPException
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

    # 全局 HTTPException → 项目统一 JSON 格式
    # 让 utils.auth.require_current_user() 内的 abort(401, description='...')
    # 不再返回 Flask 默认 HTML，而是 {code, message, data} 形式
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return jsonify({
            'code': e.code,
            'message': e.description or e.name,
            'data': None,
        }), e.code

    # 创建数据库表 & 种子数据
    with app.app_context():
        # 导入所有模型以确保建表
        from models.user import User
        from models.project import Project
        from models.operation_log import OperationLog  # noqa: F841
        from models.application import Application  # noqa: F841
        from models.checkin import Checkin  # noqa: F841
        from models.evaluation import Evaluation  # noqa: F841
        from models.college import College  # noqa: F841

        db.create_all()
        _ensure_columns()
        _seed_admin(User)

    return app


def _ensure_columns():
    """对已建好的表追加新字段（db.create_all 不会 ALTER 已存在表）。

    引入新字段时把映射加进 new_columns 即可，启动时会自动补齐。
    当前需要确保：
    - tb_project.lat / lng / radius_m / sign_in_window_minutes（P1-11 打卡真实性）
    - tb_checkin.abnormal_reason（P1-11 异常分类）
    - tb_user.email（P2-24 邮箱可选字段）
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)

    new_columns = {
        'tb_project': {
            'lat': 'DOUBLE NULL',
            'lng': 'DOUBLE NULL',
            'radius_m': 'INT DEFAULT 200',
            'sign_in_window_minutes': 'INT DEFAULT 30',
        },
        'tb_checkin': {
            'abnormal_reason': 'VARCHAR(100) NULL',
        },
        'tb_user': {
            'email': 'VARCHAR(100) NULL',
        },
    }

    for table_name, cols in new_columns.items():
        if not inspector.has_table(table_name):
            continue
        existing = {c['name'] for c in inspector.get_columns(table_name)}
        for col_name, col_type in cols.items():
            if col_name in existing:
                continue
            try:
                db.session.execute(text(
                    f'ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}'
                ))
                db.session.commit()
            except Exception:
                db.session.rollback()


def _seed_admin(User):
    """初始化管理员账号（仅在不存在时创建）。

    同时确保"管理部门"学院记录存在并把 admin.college_id 设上，
    避免出现 college_id 为 NULL 导致统计按学院分组时漏掉 admin 的情况。
    """
    if User.query.filter_by(username='admin').first():
        return

    from models.college import College
    college = College.query.filter_by(name='管理部门').first()
    if not college:
        college = College(name='管理部门', sort_order=999)
        db.session.add(college)
        db.session.flush()  # 立即拿到 college.id

    admin = User(
        username='admin',
        real_name='系统管理员',
        student_id='000000',
        college='管理部门',
        college_id=college.id,
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

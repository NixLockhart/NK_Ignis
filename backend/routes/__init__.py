def register_blueprints(app):
    """注册所有蓝图"""
    from routes.auth import auth_bp
    from routes.project import project_bp
    from routes.application import application_bp
    from routes.checkin import checkin_bp
    from routes.evaluation import evaluation_bp
    from routes.statistics import statistics_bp
    from routes.export import export_bp
    from routes.log import log_bp
    from routes.certificate import certificate_bp
    from routes.ai import ai_bp
    from routes.college import college_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(project_bp)
    app.register_blueprint(application_bp)
    app.register_blueprint(checkin_bp)
    app.register_blueprint(evaluation_bp)
    app.register_blueprint(statistics_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(certificate_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(college_bp)

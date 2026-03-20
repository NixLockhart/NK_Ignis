import os
from datetime import timedelta


class Config:
    # 数据库配置
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'db_nk_ignis')

    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        '?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT 配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'nk-ignis-jwt-secret-dev')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # 应用配置
    JSON_AS_ASCII = False

    # Dify AI 平台配置
    DIFY_BASE_URL = os.getenv('DIFY_BASE_URL', '')
    DIFY_QA_API_KEY = os.getenv('DIFY_QA_API_KEY', '')
    DIFY_CERT_API_KEY = os.getenv('DIFY_CERT_API_KEY', '')
    DIFY_NL_API_KEY = os.getenv('DIFY_NL_API_KEY', '')
    DIFY_RECOMMEND_API_KEY = os.getenv('DIFY_RECOMMEND_API_KEY', '')

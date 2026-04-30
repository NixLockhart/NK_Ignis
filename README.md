# 高校青年志愿者服务AI管理系统

本科毕业设计项目 — 计算机科学与技术专业

面向高校志愿服务管理场景，提供项目发布与审核、报名筛选、签到打卡与时长统计、活动评价、统计报表、证书生成、操作日志等完整业务能力，并通过 Dify 平台集成智能政策问答、自然语言数据查询、项目智能推荐、证书文案生成四项 AI 能力。

## 技术栈

- **前端**：Vue 3 + Vite + TypeScript + Element Plus + Tailwind CSS + ECharts + Pinia + Vue Router
- **后端**：Python Flask + SQLAlchemy + Flask-JWT-Extended + Flask-CORS + openpyxl
- **数据库**：MySQL 8.4（开发期）→ 达梦/openGauss（兼容验证）
- **AI 平台**：Dify（Chatflow + Workflow）
- **传输**：REST + SSE 流式输出（AI 模块）

## 角色与权限

| 角色 | 主要功能入口 |
|:---|:---|
| 学生 student | 浏览/报名项目、签到签退、个人档案、证书预览、AI 问答与推荐 |
| 志愿负责人 leader | 创建并维护项目、审核报名、确认打卡、评价学生 |
| 管理员 admin | 项目审核、用户/学院/角色管理、统计报表、自然语言查询、操作日志 |

## 环境要求

| 组件 | 版本 |
|:---|:---|
| Python | 3.9 及以上 |
| Node.js | 18 及以上 |
| MySQL | 8.0 及以上（开发期） |
| Dify | 自建部署或 Cloud 版 |

## 快速启动

### 1. 准备数据库

```sql
CREATE DATABASE db_nk_ignis CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 配置后端环境变量

```bash
cd backend
cp .env.example .env
# 按本机情况修改 .env，主要项见下表
```

`.env` 关键变量：

| 变量 | 说明 |
|:---|:---|
| `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` / `DB_NAME` | MySQL 连接信息 |
| `JWT_SECRET_KEY` | JWT 签名密钥（生产环境请使用随机长字符串） |
| `DIFY_BASE_URL` | Dify 平台 API 基址，例如 `http://localhost/v1` |
| `DIFY_QA_API_KEY` | 政策问答 Chatflow 的 API Key |
| `DIFY_CERT_API_KEY` | 证书文案 Workflow 的 API Key |
| `DIFY_NL_API_KEY` | 自然语言数据查询 Chatflow 的 API Key |
| `DIFY_RECOMMEND_API_KEY` | 项目推荐 Workflow 的 API Key |

未配置 Dify 相关变量时，AI 模块会返回提示信息但不会阻塞主流程。

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
python app.py
# 默认运行在 http://localhost:5000，初次启动会自动创建表并写入管理员种子账号
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
# 默认运行在 http://localhost:5173，已配置 /api 代理到后端
```

### 5. 默认账号

| 角色 | 用户名 | 密码 |
|:---|:---|:---|
| 管理员 | admin | admin123 |

学生与志愿负责人账号建议在登录后由管理员通过用户管理页创建并分配角色。

## 生产部署提示

- 后端建议用 Gunicorn 启动：`gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()`
- 前端 `npm run build` 产出 `dist/` 目录，由 Nginx 托管静态文件并反向代理 `/api/*` 到后端
- Dify 平台与主系统部署在同一内网，主系统通过 `DIFY_BASE_URL` 调用，避免跨公网调用 AI
- 生产环境务必更换 `JWT_SECRET_KEY`，并将 `.env` 的数据库密码改为复杂字符串

## 功能模块导航

| 模块 | 后端入口 | 前端页面 |
|:---|:---|:---|
| 注册登录与角色 | `routes/auth.py` | `views/login`、`views/register` |
| 项目管理 | `routes/project.py` | `views/project*` |
| 报名与筛选 | `routes/application.py` | `views/application` |
| 打卡与时长 | `routes/checkin.py` | `views/checkin`、`views/profile` |
| 活动评价 | `routes/evaluation.py` | 各项目详情内联评价区 |
| 统计与导出 | `routes/statistics.py`、`routes/export.py` | `views/statistics` |
| 证书与档案 | `routes/certificate.py` | `views/certificate`、`views/profile` |
| 学院管理 | `routes/college.py` | `views/admin/CollegeManage.vue` |
| 操作日志 | `routes/log.py` | `views/admin/OperationLog.vue` |
| AI 服务 | `routes/ai.py` | `components/AiFloatWidget.vue` |

## Dify 工作流配置

四个 AI 能力对应的 Dify 应用搭建步骤、知识库准备、变量定义、调试方法详见：

- `docs/Dify_AI工作流配置指南.md`

按指南创建对应应用后，把生成的 API Key 填到 `.env` 即可启用。

## 文档与设计资料

`docs/` 目录下包含：

- 第一周 ~ 第七周分模块设计说明
- 系统总体设计与详细设计说明（前期设计部分）
- 第七周合规性检查报告
- 项目完整学习教程
- 中期答辩 PPT 各版本

## 目录结构

```
Project/
├── backend/
│   ├── app.py              # 应用入口（factory + 蓝图注册 + 种子数据）
│   ├── config.py           # 配置（数据库、JWT、Dify）
│   ├── models/             # 7 个 ORM 模型
│   ├── routes/             # 11 个 Blueprint
│   ├── services/           # 业务逻辑层
│   ├── utils/              # 统一响应、日志工具
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # axios 模块化封装
│   │   ├── views/          # 按模块拆分的页面
│   │   ├── components/     # 复用组件（含 AI 悬浮窗）
│   │   ├── layout/         # 主框架布局
│   │   ├── router/         # 路由守卫
│   │   ├── stores/         # Pinia 状态管理
│   │   └── style.css
│   ├── vite.config.ts
│   └── package.json
├── docs/                   # 设计与说明文档
├── CLAUDE.md
├── LICENSE
└── README.md
```

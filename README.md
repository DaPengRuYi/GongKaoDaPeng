# 公考大鹏 (GongKaoDaPeng)

> 程序员公考提效平台 —— 别人用笔和脑子磨，我们用代码把学习与面试效率拉满。

## 技术栈

| 层 | 选型 |
| --- | --- |
| 后端 | FastAPI |
| 前端 | Vue 3 + Vite |
| ORM | SQLModel（基于 SQLAlchemy + Pydantic） |
| 日志 | loguru |
| 配置 | YAML（config.yaml） |
| 数据库 | 开发期 SQLite，可平滑切 PostgreSQL / MySQL |

## 目录结构

```
GongKaoDaPeng/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── main.py       # 应用入口（lifespan + CORS + 路由）
│   │   ├── config.py     # 读取 config.yaml
│   │   ├── logging_conf.py  # loguru 配置（控制台 + 文件滚动）
│   │   ├── database.py   # SQLModel 引擎与会话
│   │   ├── models.py     # SQLModel 模型（User / Question）
│   │   ├── schemas.py    # 首页响应模型
│   │   └── routers/
│   │       └── home.py   # /api/home 首页数据接口
│   ├── config.yaml       # 配置中心
│   ├── requirements.txt
│   └── run.py            # 开发启动入口
└── frontend/             # Vue 3 + Vite 前端
    ├── index.html
    ├── vite.config.js    # /api 代理到 8000
    └── src/
        ├── App.vue
        ├── main.js
        ├── style.css
        ├── api/home.js   # 首页数据请求
        └── components/Home.vue  # 首页
```

## 快速开始

### 后端

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
# 访问 http://localhost:8000  docs: http://localhost:8000/docs
```

首页数据接口：`GET /api/home`

### 前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

前端通过 Vite 代理把 `/api` 转发到后端 `8000`，开发期无需处理跨域。

## 首页数据

首页文案由后端 `/api/home` 下发，前端纯展示，便于后续接数据库 / CMS 动态化。

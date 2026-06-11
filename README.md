# Smart Community Waste Overflow Monitoring System

> 智慧社区垃圾溢出监控系统

## 项目介绍

通过部署在垃圾桶内的物联网传感器实时监测填充率，当桶溢出阈值时自动派发清洁任务，并通过完整的任务状态机管理清洁工执行流程。

### 核心功能

- 社区基础数据管理：楼栋 / 垃圾桶 / 用户 / 角色
- 传感器数据接入：实时上报桶填充率，自动触发派单
- 任务全生命周期管理：pending → in_progress → completed → rated
- 清洁工任务调度：M:N 楼栋负责 + 管理员手动指派
- 评分体系：管理员对完成任务进行 1-5 星评分
- 多维度统计：任务状态、清洁工绩效、桶溢出分布

## 技术栈

- **后端**：Python 3.11 · FastAPI · SQLAlchemy 2.0 (async) · MySQL 8.0
- **认证**：JWT · bcrypt
- **前端**：React 18 · TypeScript · Vite · Ant Design 5
- **图片存储**：腾讯云 COS（前端直传）

## 项目结构

```
waste-overflow-monitor/
├── core/           # 配置、数据库、安全、依赖注入
├── models/         # SQLAlchemy ORM 模型
├── schemas/        # Pydantic 请求/响应 schema
├── crud/           # 数据访问层
├── routers/        # HTTP 路由层
├── services/       # 跨模块业务逻辑（自动派单）
├── main.py
├── seed_demo.sql   # 演示数据脚本
└── .env.example
```

## 快速启动

```bash
# 1. 配置环境变量
cp .env.example .env   # 填写 DATABASE_URL 和 SECRET_KEY

# 2. 初始化数据库
mysql -u root -p < schema.sql

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
uvicorn main:app --reload
```

Swagger 文档：`http://localhost:8000/docs`

## 接口概览

| 模块 | 接口数 | 说明 |
|------|--------|------|
| Auth | 2 | 登录、获取当前用户 |
| Blocks | 5 | 楼栋 CRUD |
| Bins | 7 | 垃圾桶 CRUD + 传感器上报 + 状态统计 |
| Users | 8 | 用户 CRUD + 重置密码 + 改自己密码 + 绩效统计 |
| Cleaners | 4 | 清洁工楼栋分配 |
| Tasks | 9 | 任务 CRUD + 指派 + 接受 + 上报 + 评分 |
| Roles | 6 | 角色 CRUD |

## 任务状态机

```
pending → (assign) → pending[cleaner_id set]
pending → (accept)  → in_progress
in_progress → (report) → completed
completed   → (rate)   → rated
rated       → (rate)   → rated  (re-rate)
```

## 业务亮点

- **Eager-loaded SQLAlchemy relationships**（selectinload）消除 N+1 查询
- **状态机校验**：Task 状态转换非法时 400 拒绝
- **自动派单**：桶填充率 ≥ 90% 时服务层自动创建 pending 任务
- **传感器认证**：X-Sensor-Key header 防伪造数据
- **角色权限**：Admin / Cleaner 双角色，JWT + 依赖注入

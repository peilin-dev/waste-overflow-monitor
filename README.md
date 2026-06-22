# Smart Community Waste Overflow Monitoring System

> 智慧社区垃圾溢出监控系统 — 后端 API

## 项目介绍

通过部署在垃圾桶内的物联网传感器实时监测填充率，当桶溢出阈值时自动派发清洁任务，并通过完整的任务状态机管理清洁工执行流程。

- 传感器数据接入：实时上报桶填充率，自动触发派单
- 任务全生命周期：pending → in_progress → completed → rated
- 清洁工任务调度：M:N 楼栋负责制 + 管理员手动指派
- 评分体系：管理员对完成任务进行 1-5 星评分

## 技术栈

- **后端**：Python 3.11 · FastAPI · SQLAlchemy 2.0 (async) · MySQL 8.0
- **认证**：JWT · bcrypt
- **前端**（独立仓库）：React 18 · TypeScript · Vite · Ant Design 5
- **部署**：Docker Compose · GitHub Actions CI/CD · 腾讯云

## 项目结构

```
waste-overflow-monitor/
├── core/
│   ├── config.py        # 环境变量读取（.env → settings 对象）
│   ├── database.py      # 数据库连接、AsyncSessionLocal、get_db 依赖
│   ├── security.py      # hash_password、verify_password、JWT 签发/解析
│   └── deps.py          # FastAPI 依赖：get_current_user、get_current_admin
├── models/
│   ├── user.py          # user 表（管理员 + 清洁工）
│   ├── block.py         # block 表（楼栋）
│   ├── bin.py           # bin 表（垃圾桶）
│   ├── task.py          # task 表（清洁任务）
│   ├── cleaner_block.py # cleaner_block 表（清洁工-楼栋关联）
│   └── role.py          # role 表（角色定义）
├── schemas/
│   ├── auth.py          # 登录请求/响应
│   ├── task.py          # 任务请求/响应
│   └── ...              # 其他模块同理
├── routers/
│   ├── auth.py          # /api/auth/*
│   ├── tasks.py         # /api/tasks/*
│   └── ...              # 其他模块同理
├── services/
│   └── task_service.py  # 自动派单业务逻辑
├── scripts/
│   └── init_db.py       # 初始化演示数据
├── main.py              # 入口，注册所有路由
├── docker-compose.yml   # 生产部署（拉取 GHCR 镜像）
└── .env.example
```

---

## 本地开发环境

> 使用 PyCharm 的同学请看：[docs/local-setup.md](docs/local-setup.md)

**前置条件**：Python 3.11、MySQL 8.0

```bash
# 1. 克隆代码
git clone https://github.com/peilin-dev/waste-overflow-monitor.git
cd waste-overflow-monitor

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入本地 MySQL 的账号密码
```

在 MySQL 中创建数据库：

```sql
CREATE DATABASE waste_monitor CHARACTER SET utf8mb4;
```

启动后端：

```bash
uvicorn main:app --reload
```

初始化演示数据（只需跑一次）：

```bash
python scripts/init_db.py
```

启动完成后：

- API 文档：http://localhost:8000/docs
- 管理员账号：`admin / admin123`
- 清洁工账号：`liwei / zhangming / wangfang`，密码均为 `cleaner123`

> 修改代码后自动热重载，无需重启。

---

## 接口概览

所有接口前缀 `/api`，需要在 Header 带 `Authorization: Bearer <token>`（登录接口除外）。

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| Auth | POST | `/api/auth/login` | 登录，返回 JWT token |
| Auth | GET  | `/api/auth/me` | 获取当前登录用户信息 |
| Blocks | GET | `/api/blocks` | 楼栋列表 |
| Bins | GET | `/api/bins` | 垃圾桶列表（含填充率） |
| Users | GET | `/api/users` | 用户列表 |
| Cleaners | GET | `/api/cleaners/{id}/blocks` | 清洁工负责的楼栋 |
| Tasks | GET | `/api/tasks` | 任务列表（支持 `cleaner_id` 筛选） |
| Tasks | POST | `/api/tasks/{id}/accept` | 清洁工接受任务 |
| Tasks | POST | `/api/tasks/{id}/report` | 清洁工提交完成 |
| Tasks | POST | `/api/tasks/{id}/rate` | 管理员评分 |

完整接口文档见 http://localhost:8000/docs（启动后访问）。

### 登录示例

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "liwei", "password": "cleaner123"}'
```

返回：
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 2, "name": "Li Wei", "role": "cleaner", ... }
}
```

JWT payload 中包含 `role` 字段，可用于客户端区分 `admin` / `cleaner`。

---

## 任务状态机

```
pending ──(cleaner accepts)──→ in_progress ──(cleaner reports)──→ completed ──(admin rates)──→ rated
```

---

## 数据库说明

数据库：MySQL 8.0，库名 `waste_monitor`

| 表名 | 说明 |
|------|------|
| `user` | 用户（管理员 + 清洁工） |
| `block` | 楼栋 |
| `bin` | 垃圾桶 |
| `task` | 清洁任务 |
| `cleaner_block` | 清洁工 ↔ 楼栋 多对多关联 |
| `role` | 角色定义 |

详细字段及建表语句见队友交接文档。

---

## 扩展开发指南

### 新增路由

以新增"打卡"模块为例，共三步：

**第一步：** 新建 `routers/checkin.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/api/checkin", tags=["checkin"])

@router.post("")
async def checkin(
    current_user: User = Depends(get_current_user),  # 需要登录
    db: AsyncSession = Depends(get_db),
):
    # 写你的业务逻辑
    return {"message": "ok"}
```

**第二步：** 在 `main.py` 注册路由（参考已有写法）

```python
from routers import checkin as checkin_router
app.include_router(checkin_router.router)
```

**第三步：** 代码保存后自动热重载，访问 http://localhost:8000/docs 可以看到新接口。

---

### 新增数据表

以新建"打卡记录"表为例：

**第一步：** 新建 `models/checkin.py`

```python
from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class Checkin(Base):
    __tablename__ = "checkin"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cleaner_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("task.id"), nullable=False)
    photo_url: Mapped[str] = mapped_column(String(500), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
```

**第二步：** 在 `main.py` import 该模型（让 SQLAlchemy 注册到它）

```python
from models import checkin  # noqa: F401
```

**第三步：** 重启后端，`create_all` 自动建表，无需手动操作。

---

### 新增字段到已有表

SQLAlchemy 不会自动修改已有表，需要手动执行 `ALTER TABLE`。

**本地：**
```bash
mysql -u root -p waste_monitor
ALTER TABLE task ADD COLUMN photo_url VARCHAR(500);
```

**部署到服务器后**，同样需要在服务器上执行一次，否则后端报错：
```bash
# SSH 登录服务器后执行
docker exec -it waste_db mysql -uroot -p waste_monitor
ALTER TABLE task ADD COLUMN photo_url VARCHAR(500);
```

---

### 权限控制

```python
from core.deps import get_current_user, get_current_admin

# 需要登录（admin 和 cleaner 都可以）
async def my_endpoint(current_user: User = Depends(get_current_user)):
    ...

# 仅 admin 可访问
async def admin_only(current_user: User = Depends(get_current_admin)):
    ...
```

---

## 部署

推送到 `master` 分支后 GitHub Actions 自动构建镜像并部署到服务器，无需手动操作。

如需手动触发部署：在 GitHub → Actions → Deploy 页面点击 `Run workflow`。

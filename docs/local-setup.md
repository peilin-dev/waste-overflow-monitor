# 本地开发环境搭建（PyCharm）

## 前置要求

- PyCharm
- MySQL 8.0+（Navicat 或 MySQL Workbench 管理）
- Git

---

## 步骤

### 1. 克隆项目

PyCharm 菜单：**File → New Project from Version Control**

填入地址：
```
https://github.com/peilin-dev/waste-overflow-monitor.git
```

克隆完成后，右下角点击分支名，切换到 `dev`。

### 2. 配置虚拟环境 & 安装依赖

PyCharm 打开项目后会自动检测 `requirements.txt`，弹出提示直接点 **Install** 即可。

如果没有弹出：**File → Settings → Project → Python Interpreter → Add Interpreter → Virtualenv**，创建后再右键 `requirements.txt` → **Install All Packages**。

### 3. 建数据库

打开 Navicat，连接本地 MySQL，新建数据库：

- 数据库名：`waste_monitor`
- 字符集：`utf8mb4`

### 4. 配置 .env

在 PyCharm 左侧文件树中，右键 `.env.example` → **Copy**，粘贴改名为 `.env`。

编辑 `.env`，只需修改这两行（其他行不用动）：

```env
DATABASE_URL=mysql+aiomysql://root:你的MySQL密码@localhost:3306/waste_monitor
SECRET_KEY=任意一段长字符串随便填
```

> `DATABASE_URL` 里的 `root` 是 MySQL 用户名，`你的MySQL密码` 换成你自己的密码。

### 5. 启动项目

PyCharm 底部打开 **Terminal**，输入：

```bash
uvicorn main:app --reload
```

看到 `Application startup complete` 说明启动成功，数据库表已自动创建。

### 6. 初始化测试数据

左侧找到 `scripts/init_db.py`，右键 → **Run**。

---

## 验证

浏览器访问 `http://localhost:8000/docs`

测试账号：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 清洁工 | liwei | cleaner123 |
| 清洁工 | zhangming | cleaner123 |
| 清洁工 | wangfang | cleaner123 |

---

## 分支说明

- 日常开发提交到 `dev`
- `master` 只用于上线，不要直接提交

每次开发前同步最新代码：右下角点分支名 → **Update Project**

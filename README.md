# AI Name - 智能起名后端

AI Name 是一个基于 FastAPI、SQLAlchemy 异步 ORM、Redis 和 DeepSeek 的智能起名后端项目。它提供了用户注册、登录、JWT 鉴权、邮箱验证码、AI 起名生成以及基础积分系统。

## 项目定位

这个项目的目标是把“姓名起名”流程做成一个可扩展的后端服务，支持：

- 用户注册与登录
- 邮箱验证码校验
- Access Token / Refresh Token 鉴权
- 基于 DeepSeek 的智能起名
- 注册赠送起名次数，并在起名成功后扣减次数
- 通过 Swagger / ReDoc 直接测试接口

## 已实现功能

- 邮箱验证码发送，验证码保存到 Redis，默认 5 分钟有效
- 注册时校验邮箱是否已存在、验证码是否正确
- 使用 `pwdlib` 对密码进行哈希存储
- 用户登录并签发 Access Token、Refresh Token
- 使用 Bearer Token 访问受保护接口
- 支持 Access Token 验证与 Refresh Token 刷新
- DeepSeek 生成结构化起名结果（姓名、出处、寓意）
- 注册成功后赠送 3 次起名机会
- 起名成功后扣减 1 次次数，并记录积分流水
- 使用 SQLAlchemy 2.x 异步 ORM + Alembic 数据库迁移
- 提供 Windows 启动脚本与 VS Code HTTP 测试文件

## 技术栈

- Web 框架：FastAPI、Uvicorn
- 数据校验：Pydantic
- 数据库：MySQL、SQLAlchemy Async、aiomysql
- 数据库迁移：Alembic
- 缓存：Redis、redis-py AsyncIO
- 身份认证：PyJWT、HTTP Bearer
- 密码安全：pwdlib
- 邮件发送：fastapi-mail、aiosmtplib
- AI 能力：DeepSeek、LangChain、langchain-deepseek
- 配置管理：python-dotenv

## 项目结构

```text
ai_name/
├── alembicdb/                  # Alembic 迁移脚本与环境
├── core/
│   ├── authtools.py           # JWT 生成、解析与鉴权依赖
│   ├── mailtool.py            # 邮件客户端配置
│   ├── nametools.py           # DeepSeek 起名链与重试逻辑
│   └── redistools.py          # Redis 连接与依赖注入
├── models/
│   ├── __init__.py            # 数据库引擎、SessionFactory 与 Base
│   ├── user.py                # 用户模型
│   └── user_credit.py         # 用户积分与流水模型
├── repository/
│   ├── credit_repo.py         # 积分相关仓储逻辑
│   └── user_repo.py           # 用户相关仓储逻辑
├── routers/
│   ├── auth_router.py         # 注册、登录、验证码、Token 接口
│   ├── credit_router.py       # 查询剩余起名次数接口
│   └── name_router.py         # 起名接口
├── schemas/
│   ├── credit_schemas.py      # 积分相关响应模型
│   ├── name_schemas.py        # 起名请求/响应模型
│   └── user_schemas.py        # 用户/认证相关模型
├── settings/
│   └── __init__.py            # Token 过期时间配置
├── dependencies.py            # 数据库会话与邮箱依赖
├── main.py                    # FastAPI 应用入口
├── start.bat                  # Windows 一键启动脚本
├── test.http                  # VS Code REST Client 请求示例
├── alembic.ini                # Alembic 配置文件
└── .env                       # 本地环境变量，不要提交到 Git
```

## 环境要求

- Python 3.11+
- MySQL 8.x
- Redis 5.x+
- 可用的 SMTP 邮箱账号
- DeepSeek API Key

## 快速开始

### 1. 克隆项目

```bash
git clone <你的仓库地址>
cd ai_name
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
```

Windows PowerShell 激活：

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. 安装依赖

```bash
pip install fastapi uvicorn sqlalchemy aiomysql alembic redis fastapi-mail aiosmtplib pwdlib pyjwt python-dotenv pydantic email-validator langchain langchain-deepseek
```

### 4. 创建 MySQL 数据库

```sql
CREATE DATABASE ai_name
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

### 5. 配置环境变量

在项目根目录创建 `.env`：

```env
DB_URI=mysql+aiomysql://root:your_password@127.0.0.1:3306/ai_name?charset=utf8mb4

MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_smtp_authorization_code
MAIL_FROM=your_email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com
MAIL_FROM_NAME=AI Name
MAIL_STARTTLS=True
MAIL_SSL_TLS=False

JWT_SECRET_KEY=replace_with_a_long_random_secret
DEEPSEEK_API_KEY=replace_with_your_deepseek_api_key
```

你可以用下面的命令生成一个 JWT 密钥：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 6. 执行数据库迁移

```bash
alembic upgrade head
```

### 7. 启动 Redis

确认 Redis 正常运行：

```bash
redis-cli ping
```

预期返回：

```text
PONG
```

### 8. 启动服务

```bash
uvicorn main:app --reload
```

Windows 用户也可以直接运行：

```bat
start.bat
```

启动后可访问：

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 接口说明

### 认证相关

| 方法 | 路径                | 说明                                 |
| ---- | ------------------- | ------------------------------------ |
| GET  | /mail/test          | 测试邮件发送                         |
| GET  | /auth/code          | 发送注册验证码                       |
| POST | /auth/register      | 用户注册                             |
| POST | /auth/login         | 登录并获取双 Token                   |
| GET  | /auth/verify-access | 验证 Access Token                    |
| POST | /auth/refresh       | 使用 Refresh Token 换新 Access Token |

### 起名与积分相关

| 方法 | 路径            | 说明                     |
| ---- | --------------- | ------------------------ |
| POST | /name/get_names | 根据条件生成智能起名方案 |
| GET  | /credit/balance | 查询当前用户剩余起名次数 |

## 请求示例

### 发送验证码

```http
GET http://127.0.0.1:8000/auth/code?email=user@example.com
```

### 注册

```http
POST http://127.0.0.1:8000/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "testuser",
  "password": "123456",
  "confirm_password": "123456",
  "code": "1234"
}
```

### 登录

```http
POST http://127.0.0.1:8000/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "123456"
}
```

登录成功后返回：

```json
{
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "user@example.com"
  },
  "access_token": "...",
  "refresh_token": "..."
}
```

### 智能起名

```http
POST http://127.0.0.1:8000/name/get_names
Content-Type: application/json
Authorization: Bearer your_access_token

{
  "surname": "陈",
  "gender": "男",
  "length": "两字",
  "other": "希望名字有文化底蕴",
  "exclude": ["伟", "强"]
}
```

返回结构：

```json
{
  "names": [
    {
      "name": "候选名字",
      "reference": "出处",
      "moral": "寓意"
    }
  ]
}
```

## 备注

- 注册成功后会自动赠送 3 次起名机会。
- 每次成功起名后会扣除 1 次机会。
- 生成起名时会调用 DeepSeek，若模型返回异常会触发重试逻辑。
  
## 后续可扩展方向

- 增加自动化测试
- 增加邮件发送频率限制
- 支持用户资料管理与密码重置
- 增加起名历史记录与收藏
- 增加 Docker / Docker Compose 部署
- 增加管理后台与权限控制

# AI Name - 智能起名后端

AI Name 是一个基于 FastAPI 与 DeepSeek 的智能起名后端项目。项目目前实现了邮箱验证码注册、用户登录、JWT 双令牌认证、Redis 验证码缓存，以及根据姓氏、性别、名字长度和用户偏好生成结构化起名方案。

每个候选名字包含名字、出处和寓意，接口通过 Pydantic 对输入与模型输出进行结构化校验。

## 已实现功能

- 邮箱验证码发送，验证码写入 Redis 并在 5 分钟后过期
- 邮箱验证码注册与重复邮箱检查
- 使用 `pwdlib` 哈希保存用户密码
- 用户邮箱、密码登录
- JWT Access Token 与 Refresh Token
- Access Token 验证与 Refresh Token 换新
- Bearer Token 接口保护
- DeepSeek 智能起名
- 起名结果结构化输出：姓名、出处、寓意
- SQLAlchemy 2.0 异步 ORM
- Alembic 数据库迁移
- Windows 一键启动脚本
- FastAPI 自动生成 Swagger / ReDoc 接口文档

## 技术栈

| 分类 | 技术 |
| --- | --- |
| Web 框架 | FastAPI、Uvicorn |
| 数据校验 | Pydantic |
| 数据库 | MySQL、SQLAlchemy Async、aiomysql |
| 数据库迁移 | Alembic |
| 缓存 | Redis、redis-py AsyncIO |
| 身份认证 | PyJWT、HTTP Bearer、HS256 |
| 密码安全 | pwdlib |
| 邮件 | fastapi-mail、aiosmtplib |
| AI | DeepSeek、LangChain |
| 配置 | python-dotenv、`.env` |

## 项目结构

```text
ai_name/
├── alembicdb/             # Alembic 迁移环境与版本文件
├── core/
│   ├── authtools.py       # JWT 创建、解析与认证依赖
│   ├── mailtool.py        # 邮件客户端配置
│   ├── nametools.py       # DeepSeek 起名链与重试逻辑
│   └── redistools.py      # Redis 异步客户端
├── models/
│   ├── __init__.py        # 数据库引擎、会话和 ORM Base
│   └── user.py            # User 模型与密码哈希逻辑
├── repository/
│   └── user_repo.py       # 用户数据访问层
├── routers/
│   ├── auth_router.py     # 验证码、注册、登录与 Token 接口
│   └── name_router.py     # 受保护的智能起名接口
├── schemas/
│   ├── name_schemas.py    # 起名请求和响应模型
│   └── user_schemas.py    # 注册、登录和 Token 数据模型
├── settings/
│   └── __init__.py        # Access / Refresh Token 有效期
├── dependencies.py        # 数据库会话与邮件依赖
├── main.py                # FastAPI 应用入口
├── start.bat              # Windows 一键启动 Redis 与 Uvicorn
├── test.http              # VS Code REST Client 测试请求
├── alembic.ini            # Alembic 配置
└── .env                   # 本地密钥配置，不应提交到 Git
```

## 工作流程

### 注册流程

1. 客户端调用验证码接口。
2. 服务端生成 4 位验证码并发送邮件。
3. 验证码以邮箱为键写入 Redis，有效期 300 秒。
4. 客户端提交邮箱、用户名、密码和验证码。
5. 服务端校验邮箱、验证码与密码字段。
6. 密码经过哈希后写入 MySQL。
7. 注册成功后删除 Redis 中的验证码，防止重复使用。

### 登录与认证流程

1. 用户提交邮箱和密码。
2. 服务端查询用户并验证密码哈希。
3. 登录成功后签发 Access Token 和 Refresh Token。
4. 客户端使用 Access Token 访问受保护接口。
5. Access Token 过期后，使用 Refresh Token 获取新的 Access Token。

默认有效期：

- Access Token：15 分钟
- Refresh Token：30 天

### 智能起名流程

1. 客户端携带 Access Token 和起名条件调用接口。
2. FastAPI 验证 Token 并取得当前用户 ID。
3. LangChain 将结构化条件发送给 DeepSeek。
4. Pydantic 校验模型输出。
5. 返回 5 个包含名字、出处和寓意的候选方案。

## 环境要求

- Python 3.11 或更高版本
- MySQL 8.x
- Redis 5.x 或更高版本
- 可用的 SMTP 邮箱账号
- DeepSeek API Key

项目中的 `start.bat` 面向 Windows，并默认 Redis 安装在：

```text
C:\Program Files\Redis
```

如果 Redis 位于其他目录，请修改 `start.bat` 中的 `REDIS_DIR`。

## 本地安装

### 1. 克隆项目

```bash
git clone git@github.com:hongyuchen982-cpu/ainame.git
cd ainame
```

也可以使用 HTTPS：

```bash
git clone https://github.com/hongyuchen982-cpu/ainame.git
cd ainame
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
```

Windows PowerShell 激活：

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows CMD 激活：

```bat
.venv\Scripts\activate.bat
```

### 3. 安装依赖

```bash
pip install fastapi uvicorn sqlalchemy aiomysql alembic redis fastapi-mail aiosmtplib pwdlib pyjwt python-dotenv pydantic email-validator langchain langchain-deepseek
```

### 4. 创建 MySQL 数据库

```sql
CREATE DATABASE ainame
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

### 5. 配置环境变量

在项目根目录创建 `.env`：

```env
# MySQL
DB_URI=mysql+aiomysql://root:your_mysql_password@127.0.0.1:3306/ainame?charset=utf8mb4

# SMTP 邮箱
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_smtp_authorization_code
MAIL_FROM=your_email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com
MAIL_FROM_NAME=AI Name
MAIL_STARTTLS=True
MAIL_SSL_TLS=False

# JWT 签名密钥
JWT_SECRET_KEY=replace_with_a_long_random_secret

# DeepSeek
DEEPSEEK_API_KEY=replace_with_your_deepseek_api_key
```

可以使用 Python 生成 JWT 随机密钥：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> `.env` 包含数据库密码、邮箱授权码和 API Key，禁止提交到 GitHub。

### 6. 执行数据库迁移

```bash
alembic upgrade head
```

### 7. 启动 Redis

确认 Redis 正常响应：

```bash
redis-cli ping
```

正确结果：

```text
PONG
```

### 8. 启动 FastAPI

```bash
uvicorn main:app --reload
```

Windows 用户也可以双击：

```text
start.bat
```

启动后访问：

- Swagger UI：<http://127.0.0.1:8000/docs>
- ReDoc：<http://127.0.0.1:8000/redoc>

## API 接口

| 方法 | 路径 | 是否认证 | 功能 |
| --- | --- | --- | --- |
| GET | `/mail/test` | 否 | 测试邮件发送 |
| GET | `/auth/code` | 否 | 发送注册验证码 |
| POST | `/auth/register` | 否 | 用户注册 |
| POST | `/auth/login` | 否 | 用户登录并获取双 Token |
| GET | `/auth/verify-access` | Access Token | 验证 Access Token |
| POST | `/auth/refresh` | Refresh Token | 获取新的 Access Token |
| POST | `/name/get_names` | Access Token | 生成智能起名方案 |

## 请求示例

### 获取注册验证码

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
  "surname": "张",
  "gender": "男",
  "length": "两字",
  "other": "希望名字大气，有文化底蕴",
  "exclude": ["伟", "强"]
}
```

返回结构：

```json
{
  "names": [
    {
      "name": "候选名字",
      "reference": "文学或文化出处",
      "moral": "名字寓意"
    }
  ]
}
```

### 刷新 Access Token

```http
POST http://127.0.0.1:8000/auth/refresh
Authorization: Bearer your_refresh_token
```

## 安全说明

- 密码只保存哈希值，不保存明文。
- JWT 使用服务端密钥签名，密钥只存放在 `.env`。
- 注册验证码 5 分钟后自动过期，注册成功后立即删除。
- 不要在 JWT Payload 中保存密码、密钥等敏感信息。
- 生产环境应启用 HTTPS，并限制 CORS 来源。
- 生产环境应关闭 SQLAlchemy 的 `echo=True` 和 Uvicorn 的 `--reload`。
- 建议为验证码发送接口增加频率限制，避免邮件滥用。

## 开发状态

项目目前处于学习和持续开发阶段。后续可以继续完善：

- 自动化测试
- Docker / Docker Compose 部署
- 邮件验证码发送频率限制
- 用户资料与密码重置
- 统一异常响应和日志系统
- 起名历史记录与收藏
- 管理员权限和内容审核
- CI/CD 与生产环境部署

## License

本项目暂未指定开源许可证。在添加许可证之前，默认保留全部权利。

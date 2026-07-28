# AI Name - 智能起名后端

AI Name 是一个基于 FastAPI、SQLAlchemy 异步 ORM、Redis、DeepSeek 和 LangGraph 的智能起名后端项目。它提供用户认证、多场景 AI 起名、用户专属 RAG 知识库、起名次数管理、套餐购买和支付宝支付能力。

## 项目定位

这个项目的目标是把“姓名起名”流程做成一个可扩展的后端服务，支持：

- 用户注册与登录
- 邮箱验证码校验
- Access Token / Refresh Token 鉴权
- 基于 LangGraph 和 DeepSeek 的多场景智能起名
- 支持人名、企业名和宠物名三类命名场景
- 上传 TXT/PDF 文件，构建按用户隔离的 RAG 知识库
- 注册赠送起名次数，并在起名成功后扣减次数
- 查询套餐、创建订单并通过支付宝购买起名次数
- 通过 Swagger / ReDoc 直接测试接口

## 已实现功能

- 邮箱验证码发送，验证码保存到 Redis，默认 5 分钟有效
- 注册时校验邮箱是否已存在、验证码是否正确
- 使用 `pwdlib` 对密码进行哈希存储
- 用户登录并签发 Access Token、Refresh Token
- 使用 Bearer Token 访问受保护接口
- 支持 Access Token 验证与 Refresh Token 刷新
- LangGraph 根据命名场景路由至人名、企业名或宠物名专家节点
- DeepSeek 生成结构化起名结果（名称、出处或创作思路、寓意）
- 企业命名支持检索用户上传的私有资料，结合品牌规范生成候选名称
- 支持上传 TXT/PDF 文件，并通过 Chroma 和 Ollama Embeddings 构建用户专属知识库
- 注册成功后赠送 3 次起名机会
- 起名成功后扣减 1 次次数，并记录积分流水
- 支持上架套餐查询、订单创建和订单状态查询
- 支持支付宝网页支付、同步回跳验签和异步通知处理
- 支付成功后自动增加起名次数，并通过订单状态和数据库锁避免重复入账
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
- AI 工作流：LangGraph
- 大语言模型：DeepSeek、LangChain、langchain-deepseek
- RAG：Chroma、langchain-chroma、langchain-community
- 向量模型：Ollama、qwen3-embedding:4b
- 支付：支付宝开放平台、python-alipay-sdk
- 配置管理：python-dotenv

## 项目结构

```text
ai_name/
├── alembicdb/                  # Alembic 迁移脚本与环境
├── core/
│   ├── authtools.py           # JWT 生成、解析与鉴权依赖
│   ├── alipaytools.py         # 支付宝客户端与支付地址配置
│   ├── mailtool.py            # 邮件客户端配置
│   ├── nametools.py           # DeepSeek 起名链与重试逻辑
│   ├── rag_service.py         # 文档切片、向量化与用户知识检索
│   ├── redistools.py          # Redis 连接与依赖注入
│   └── workflow.py            # LangGraph 多场景起名工作流
├── models/
│   ├── __init__.py            # 数据库引擎、SessionFactory 与 Base
│   ├── package.py             # 起名次数套餐模型
│   ├── user.py                # 用户模型
│   ├── user_credit.py         # 用户积分与流水模型
│   └── user_order.py          # 用户支付订单模型
├── repository/
│   ├── credit_repo.py         # 积分相关仓储逻辑
│   ├── order_repo.py          # 订单创建、查询与支付入账逻辑
│   ├── package_repo.py        # 套餐查询逻辑
│   └── user_repo.py           # 用户相关仓储逻辑
├── routers/
│   ├── auth_router.py         # 注册、登录、验证码、Token 接口
│   ├── credit_router.py       # 查询剩余起名次数接口
│   ├── name_router.py         # 多场景起名接口
│   ├── package_router.py      # 套餐查询接口
│   ├── pay_router.py          # 下单、订单查询与支付宝回调接口
│   └── rag_router.py          # 用户知识库文件上传接口
├── schemas/
│   ├── credit_schemas.py      # 积分相关响应模型
│   ├── name_schemas.py        # 起名请求/响应模型
│   ├── package_schemas.py     # 套餐响应模型
│   ├── pay_schemas.py         # 支付与订单模型
│   └── user_schemas.py        # 用户/认证相关模型
├── chroma_rag_db/             # Chroma 本地向量库，不提交到 Git
├── uploads/                   # 用户上传文件，不提交到 Git
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
- Ollama，并已下载 `qwen3-embedding:4b` 模型
- 可用的 SMTP 邮箱账号
- DeepSeek API Key
- 支付宝开放平台应用（如需测试支付功能）

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
pip install fastapi uvicorn sqlalchemy aiomysql alembic redis fastapi-mail aiosmtplib pwdlib pyjwt python-dotenv pydantic email-validator langchain langchain-deepseek langgraph langchain-chroma langchain-community langchain-ollama chromadb pypdf python-multipart python-alipay-sdk
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

# 支付宝开放平台配置
ALIPAY_APP_ID=your_alipay_app_id
ALIPAY_APP_PRIVATE_KEY=your_app_private_key_without_header
ALIPAY_PUBLIC_KEY=your_alipay_public_key_without_header
ALIPAY_GATEWAY=your_alipay_gateway_url
ALIPAY_RETURN_URL=http://127.0.0.1:8000/pay/success
ALIPAY_NOTIFY_URL=https://your-public-domain.example.com/pay/alipay_notify
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

### 8. 准备本地向量模型

安装并启动 Ollama 后下载项目使用的 Embedding 模型：

```bash
ollama pull qwen3-embedding:4b
```

只有企业命名和知识库功能需要使用该模型。人名、宠物名仍可直接调用 DeepSeek 工作流。

### 9. 启动服务

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

### 知识库相关

| 方法 | 路径              | 鉴权 | 说明                                      |
| ---- | ----------------- | ---- | ----------------------------------------- |
| POST | /knowledge/upload | 是   | 上传 TXT/PDF 文件并在后台构建用户专属知识库 |

### 套餐与支付相关

| 方法 | 路径                    | 鉴权 | 说明                         |
| ---- | ----------------------- | ---- | ---------------------------- |
| GET  | /package/list           | 否   | 查询当前已上架的套餐         |
| POST | /pay/create_order       | 是   | 创建订单并返回支付宝支付地址 |
| GET  | /pay/order/{order_no}   | 是   | 查询当前用户的订单状态       |
| GET  | /pay/success            | 否   | 支付宝浏览器同步回跳地址     |
| POST | /pay/alipay_notify      | 否   | 支付宝服务器异步通知地址     |

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
  "category": "人名",
  "surname": "陈",
  "gender": "男",
  "length": "两字",
  "other": "希望名字有文化底蕴",
  "exclude": ["伟", "强"]
}
```

`category` 可选值为 `人名`、`企业名`、`宠物名`。生成人名时必须填写 `surname`；企业名和宠物名可以留空。

企业命名示例：

```json
{
  "category": "企业名",
  "surname": "",
  "gender": "不限",
  "length": "不限",
  "other": "面向年轻用户的 AI 智能硬件品牌",
  "exclude": []
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

### 上传用户知识库

仅支持 TXT 和 PDF 文件。文件解析和向量化由后台任务完成，接口返回成功后需等待片刻再发起企业命名请求。

```http
POST http://127.0.0.1:8000/knowledge/upload
Authorization: Bearer your_access_token
Content-Type: multipart/form-data; boundary=WebAppBoundary

--WebAppBoundary
Content-Disposition: form-data; name="file"; filename="company_rules.txt"
Content-Type: text/plain

< ./company_rules.txt
--WebAppBoundary--
```

### 创建支付订单

先通过 `GET /package/list` 获取套餐 ID，再创建订单：

```http
POST http://127.0.0.1:8000/pay/create_order
Content-Type: application/json
Authorization: Bearer your_access_token

{
  "package_id": 1
}
```

响应中的 `pay_url` 是支付宝收银台地址。支付完成后，可使用返回的 `order_no` 查询订单状态。

## 备注

- 注册成功后会自动赠送 3 次起名机会。
- 每次成功起名后会扣除 1 次机会。
- 企业命名会优先检索当前用户的专属知识库，不同用户的数据使用独立 Chroma Collection 隔离。
- `/pay/alipay_notify` 必须能够被支付宝服务器公网访问，不能添加 Bearer Token 鉴权。
- 支付入账以验签、订单金额和订单状态为依据；异步通知是生产环境的主要入账方式。
- 数据库迁移只创建套餐和订单表，不会自动插入套餐数据；使用支付接口前需先在 `package` 表中添加上架套餐。
- `.env`、`uploads/`、`chroma_rag_db/` 和 Python 缓存均已加入 Git 忽略规则。
  
## 后续可扩展方向

- 增加自动化测试
- 增加邮件发送频率限制
- 支持用户资料管理与密码重置
- 增加起名历史记录与收藏
- 增加套餐和订单管理后台
- 将上传文件和向量数据库迁移到对象存储与独立向量服务
- 增加 Docker / Docker Compose 部署
- 增加管理后台与权限控制

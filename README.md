# 一念 AI Name - 智能起名全栈应用

一念 AI Name 是一个完整的智能起名 Web 应用。前端使用 React、Vite 和 Node.js，后端使用 FastAPI、SQLAlchemy 异步 ORM、Redis、DeepSeek 与 LangGraph。项目提供用户认证、多场景 AI 起名、基于 PostgreSQL Checkpoint 的多轮微调、用户专属 RAG 知识库、企业域名可用性查询、AI Logo 生成、起名次数管理、套餐购买和支付宝支付能力。

## 项目定位

这个项目的目标是把“智能起名”流程做成一个可直接使用、可继续扩展的全栈产品，支持：

- 用户注册与登录
- 邮箱验证码校验
- Access Token / Refresh Token 鉴权
- 未登录用户只能访问登录/注册入口，认证成功后才能进入应用
- 基于 LangGraph 和 DeepSeek 的多场景智能起名
- 支持人名、企业名和宠物名三类命名场景
- 上传 TXT/PDF 文件，构建按用户隔离的 RAG 知识库
- 为企业候选名生成 `.com` 域名并查询注册状态
- 从 5 个候选名中确认并持久化 1 个最终名称
- 为已选定的企业名称使用通义万相生成 Logo 图形
- 为最终企业名称生成品牌定位、Slogan、Logo 概念、视觉规范、域名矩阵和风险提示
- 汇总项目条件、候选轮次、最终选名、名称校验和品牌资产，生成可鉴权下载的中文 PDF 命名报告
- 注册赠送起名次数，并在起名成功后扣减次数
- 查询套餐、创建订单并通过支付宝购买起名次数
- 响应式 Web 前端，适配桌面和移动设备
- 独立 Vue 3 uni-app 移动端，可通过 HBuilderX 打包 Android APK
- Access Token 失效后通过 Refresh Token 自动续期
- 通过 Swagger / ReDoc 直接测试接口

## 已实现功能

- 邮箱验证码发送，验证码保存到 Redis，默认 5 分钟有效
- 注册时校验邮箱是否已存在、验证码是否正确
- 使用 `pwdlib` 对密码进行哈希存储
- 用户登录并签发 Access Token、Refresh Token
- 用户资料与头像修改、修改密码、邮箱验证码找回密码
- 用户中心提供统一个人工作台，汇总次数、流水、命名项目、订单、知识库和 PDF 报告
- 最近三份命名报告可在用户中心直接通过鉴权接口下载
- 运营后台统一汇总用户、项目、订单、收入、报告、知识库和运行中任务
- 管理员可查询全平台命名项目，并按草稿、生成中、已选名和归档状态筛选
- 登录设备和登录记录管理，支持主动撤销设备会话
- 账号冻结后禁止登录并立即使已有 Token 失效
- 内置普通用户/管理员角色和 RBAC 权限控制
- 管理员用户冻结、角色分配、权限配置和操作审计接口
- 使用 Bearer Token 访问受保护接口
- 支持 Access Token 验证与 Refresh Token 刷新
- LangGraph 根据命名场景路由至人名、企业名或宠物名专家节点
- DeepSeek 生成结构化起名结果（名称、出处或创作思路、寓意）
- 使用 PostgreSQL 持久化 LangGraph Checkpoint，并通过 `thread_id` 支持多轮反馈和名字微调
- PostgreSQL 异步连接池、Saver 和工作流均由 FastAPI lifespan 统一初始化与释放
- 最终选择写入 MySQL，并验证候选名、命名会话和登录用户之间的归属关系
- 首次生成自动创建命名项目，保存命名条件、每轮候选与反馈历史
- 支持项目列表、详情、名称修改、状态筛选、最终选名、归档和恢复
- 企业命名支持检索用户上传的私有资料，结合品牌规范生成候选名称
- 支持上传 TXT/PDF 文件，通过 RabbitMQ 投递异步任务，并由独立 Worker 构建知识库
- 通过 Chroma 和 Ollama Embeddings 构建按用户隔离的向量集合
- 支持知识库文件列表、处理状态、失败原因、文本块统计、删除和重新处理
- Worker 持久化排队/处理中/成功/失败状态，并用任务版本号阻止旧任务覆盖删除或重试结果
- 提供知识库运营后台、`knowledge.manage` 权限和管理员操作审计
- 提供统一异步任务表，记录任务类型、业务对象、进度、结果、失败原因和尝试次数
- 知识库 Worker 支持最多 3 次自动重试、持久化消息确认、任务心跳和超时租约接管
- 支持用户任务列表/详情/人工重试，以及管理员任务筛选、重试、取消和操作审计
- 支持 IANA RDAP 引导的多后缀域名校验，以及可配置的商标、企业和社交平台查询适配器
- 保存名称校验历史、数据覆盖率、风险评分与风险等级，未配置数据源明确显示“数据不足”
- 提供“名称校验”和“校验后台”前端入口，以及 `validations.manage` 管理权限
- 支持为最终企业名生成多版本品牌价值资产包，并关联名称校验快照
- 域名矩阵只使用真实校验结果确定性生成，不由大模型虚构可用状态
- 提供“品牌资产”和“资产后台”前端入口，以及 `brand_assets.manage` 管理权限
- 并发查询企业候选名对应 `.com` 域名的注册状态
- 仅允许已选定的企业名称调用通义万相生成 Logo，并保存生成状态与图片地址
- 注册成功后赠送 3 次起名机会
- 起名成功后幂等扣减 1 次次数，并记录带业务操作号的权益流水
- 支持失败返还、用户次数账户与流水查询、管理员手工调整次数及操作审计
- 支持上架套餐查询、订单创建和订单状态查询
- 支持套餐后台新增、修改价格与次数、上下架、排序和安全删除
- 支持支付宝网页支付、同步回跳验签和异步通知处理
- 支付成功后自动增加起名次数，并通过订单状态和数据库锁避免重复入账
- 支持订单列表、详情、继续支付、主动同步、关闭、支付交易流水和管理员退款
- 使用 SQLAlchemy 2.x 异步 ORM + Alembic 数据库迁移
- React 单页应用，覆盖首页、智能起名、我的项目、知识库、Logo、套餐和用户中心页面
- 前端使用全站登录门禁；退出登录或 Token 刷新失败后自动返回登录页
- 前端统一封装 API、登录状态、Token 自动刷新、加载状态和错误提示
- Vite 开发代理连接 FastAPI，本地开发无需额外配置 CORS
- 响应式布局，支持桌面端、平板和手机端
- 提供 Windows 启动脚本与 VS Code HTTP 测试文件

## 技术栈

### 前端

- Node.js 20.19+（Vite 8 要求）
- React 19
- Vite 8
- Lucide React
- 原生 CSS 响应式设计

### 后端与基础设施

- Web 框架：FastAPI、Uvicorn
- 数据校验：Pydantic
- 业务数据库：MySQL、SQLAlchemy Async、aiomysql
- 工作流记忆库：PostgreSQL、psycopg、psycopg-pool、langgraph-checkpoint-postgres
- 数据库迁移：Alembic
- 缓存：Redis、redis-py AsyncIO
- 身份认证：PyJWT、HTTP Bearer
- 密码安全：pwdlib
- 邮件发送：fastapi-mail、aiosmtplib
- AI 工作流：LangGraph
- 大语言模型：DeepSeek、LangChain、langchain-deepseek
- RAG：Chroma、langchain-chroma、langchain-community
- 向量模型：Ollama、qwen3-embedding:4b
- 消息队列：RabbitMQ、aio-pika
- Logo 生成：阿里云百炼、通义万相、HTTPX
- 支付：支付宝开放平台、python-alipay-sdk
- PDF 报告：ReportLab、pypdf、pdfplumber
- 配置管理：python-dotenv

## 项目结构

```text
ai_name/
├── frontend/                   # React + Vite 前端
│   ├── src/
│   │   ├── App.jsx            # 页面、组件与前端业务流程
│   │   ├── api.js             # API 请求、Token 刷新与资源地址处理
│   │   ├── dashboard.js       # 用户中心七项模块与主操作决策
│   │   ├── main.jsx           # React 入口
│   │   └── styles.css         # 视觉系统与响应式样式
│   ├── .env.example           # 前端 API 地址示例
│   ├── package.json           # Node.js 依赖与脚本
│   └── vite.config.js         # Vite 配置与本地代理
├── mobile-uniapp/              # Vue 3 uni-app 移动端（Android/iOS/H5/小程序）
│   ├── src/                    # 页面、API、配置和 manifest
│   ├── .env.example           # 真机 API 地址示例
│   └── README.md              # HBuilderX 运行与 APK 打包指南
├── alembicdb/                  # Alembic 迁移脚本与环境
├── core/
│   ├── authtools.py           # JWT 生成、解析与鉴权依赖
│   ├── alipaytools.py         # 支付宝客户端与支付地址配置
│   ├── domain_tools.py        # .com 域名注册状态查询
│   ├── logo_tools.py          # 通义万相 Logo 生成与本地保存
│   ├── brand_asset_service.py # 品牌资产 AI 生成、域名矩阵与风险快照
│   ├── report_service.py      # 中文 PDF 命名报告排版、字体嵌入与文件校验
│   ├── mailtool.py            # 邮件客户端配置
│   ├── nametools.py           # DeepSeek 起名链与重试逻辑
│   ├── rag_service.py         # 文档切片、向量化与用户知识检索
│   ├── redistools.py          # Redis 连接与依赖注入
│   └── workflow.py            # LangGraph 工作流、PostgreSQL 记忆池生命周期
├── models/
│   ├── __init__.py            # 数据库引擎、SessionFactory 与 Base
│   ├── package.py             # 起名次数套餐模型
│   ├── auth_models.py         # 角色权限、登录设备、登录记录与审计日志
│   ├── naming_project.py      # 命名项目、生成轮次与候选快照
│   ├── knowledge_file.py      # 知识库文件、处理状态与任务版本
│   ├── async_task.py          # 统一异步任务、进度、重试和租约状态
│   ├── name_validation.py     # 名称综合校验历史与风险快照
│   ├── brand_asset.py         # 品牌价值资产版本及校验快照
│   ├── naming_report.py       # 报告快照、文件摘要和用户归属
│   ├── selected_name.py       # 最终名称及其 Logo 结果
│   ├── user.py                # 用户模型
│   ├── user_credit.py         # 用户积分与流水模型
│   └── user_order.py          # 用户支付订单模型
├── repository/
│   ├── credit_repo.py         # 积分相关仓储逻辑
│   ├── order_repo.py          # 订单创建、查询与支付入账逻辑
│   ├── package_repo.py        # 套餐查询逻辑
│   ├── knowledge_repo.py      # 知识库状态流转、重试与并发保护
│   ├── task_repo.py           # 异步任务状态机、心跳、重试与取消
│   ├── validation_repo.py     # 校验历史、幂等请求和后台查询
│   ├── brand_asset_repo.py    # 品牌资产版本、幂等和后台查询
│   ├── report_repo.py         # 用户与管理员报告查询
│   ├── dashboard_repo.py      # 用户中心跨模块只读汇总
│   ├── admin_dashboard_repo.py # 运营数据与全平台项目汇总
│   ├── project_repo.py        # 命名项目、轮次、候选和归档仓储
│   ├── selected_name_repo.py  # 最终名称选择与 Logo 结果持久化
│   ├── security_repo.py       # RBAC、设备、登录记录与审计仓储
│   └── user_repo.py           # 用户相关仓储逻辑
├── routers/
│   ├── auth_router.py         # 注册、登录、验证码、Token 接口
│   ├── user_router.py         # 用户资料、密码、设备和登录记录
│   ├── admin_router.py        # 用户冻结、角色权限和管理员审计
│   ├── credit_router.py       # 查询剩余起名次数接口
│   ├── name_router.py         # 多场景起名接口
│   ├── project_router.py      # 命名项目列表、详情、修改和归档接口
│   ├── logo_router.py         # 企业 Logo 生成接口
│   ├── package_router.py      # 套餐查询接口
│   ├── pay_router.py          # 下单、订单查询与支付宝回调接口
│   ├── rag_router.py          # 知识库上传、列表、状态、删除及管理接口
│   ├── task_router.py         # 用户任务中心与管理员任务后台接口
│   ├── validation_router.py   # 名称校验与校验后台接口
│   ├── brand_asset_router.py  # 品牌价值资产与资产后台接口
│   └── report_router.py       # 报告生成、用户下载与管理员下载接口
├── schemas/
│   ├── credit_schemas.py      # 积分相关响应模型
│   ├── name_schemas.py        # 起名请求/响应模型
│   ├── logo_schemas.py        # Logo 请求/响应模型
│   ├── package_schemas.py     # 套餐响应模型
│   ├── pay_schemas.py         # 支付与订单模型
│   ├── knowledge_schemas.py   # 知识库文件响应模型
│   ├── task_schemas.py        # 异步任务响应模型
│   ├── validation_schemas.py  # 名称校验请求与风险报告模型
│   ├── brand_asset_schemas.py # 品牌资产请求、结构化内容与响应模型
│   ├── report_schemas.py      # 报告生成请求与用户/管理员响应模型
│   ├── project_schemas.py     # 命名项目请求与响应模型
│   └── user_schemas.py        # 用户/认证相关模型
├── chroma_rag_db/             # Chroma 本地向量库，不提交到 Git
├── static/logos/              # 运行时生成的 Logo 图片，不提交到 Git
├── uploads/                   # 用户上传文件，不提交到 Git
├── settings/
│   └── __init__.py            # Token 过期时间配置
├── dependencies.py            # 数据库会话与邮箱依赖
├── init_pg_memory.py          # 初始化 LangGraph PostgreSQL Checkpoint 表
├── main.py                    # FastAPI 应用入口
├── rag_worker.py              # RabbitMQ 知识库任务消费者
├── scripts/
│   ├── build_ainame_textbook.py # 教材 PDF 生成脚本
│   ├── create_admin.py        # 创建或提升首个管理员账号
│   └── generate_report_preview.py # 稳定 UTF-8 报告样本与视觉验收入口
├── output/pdf/                # 运行时报告文件与 PDF 验收样本
├── docs/ROADMAP.md            # 分阶段功能建设路线图
├── start.bat                  # Windows 一键启动脚本
├── test.http                  # VS Code REST Client 请求示例
├── test_name.http             # 多轮起名、知识库与 Logo 请求示例
├── alembic.ini                # Alembic 配置文件
└── .env                       # 本地环境变量，不要提交到 Git
```

## 环境要求

- Node.js 20.19+ 与 npm
- Python 3.11+
- MySQL 8.x
- PostgreSQL 14+（保存 LangGraph 多轮记忆）
- RabbitMQ 3.x（分发知识库解析任务）
- Redis 5.x+
- Ollama，并已下载 `qwen3-embedding:4b` 模型
- 可用的 SMTP 邮箱账号
- DeepSeek API Key
- 阿里云百炼 API Key（如需生成 Logo）
- 支付宝开放平台应用（如需测试支付功能）

## 快速开始

如果数据库、Redis、RabbitMQ 和环境变量都已经准备好，本地开发只需打开两个终端：

Windows 本机推荐直接双击项目根目录的 `start.bat`。它会检查并尝试启动
MySQL、PostgreSQL、Redis 和 RabbitMQ Windows 服务，执行数据库迁移与记忆表初始化，
然后分别打开 FastAPI、RAG Worker 和 React 三个运行窗口。基础服务作为 Windows 服务运行，
不需要额外保留四个终端；前后端就绪后会自动打开浏览器。只检查环境而不启动应用可执行：

```powershell
.\start.bat --check
```

如果暂时不想自动打开浏览器，可以执行 `.\start.bat -NoBrowser`。

如果 `.env` 没有设置 `RABBITMQ_URL`，脚本在本次本地启动中使用
`amqp://guest:guest@127.0.0.1:5672/`；修改过 RabbitMQ 账号时必须在 `.env` 明确配置。

终端 1，启动 FastAPI 后端：

```powershell
cd ai_name
python run_server.py --reload
```

终端 2，启动 React 前端：

```powershell
cd ai_name\frontend
npm install
npm run dev
```

浏览器访问 `http://127.0.0.1:5173`。后端接口文档位于 `http://127.0.0.1:8000/docs`。

移动端另有独立 Vue 3 uni-app 工程 `mobile-uniapp`，可用 HBuilderX 运行到 H5、Android、iOS 或小程序。详细使用方式见 `mobile-uniapp/README.md`。

### 移动端 APK 打包与真机登录

1. 运行根目录 `start.bat`，确保 FastAPI 显示监听 `0.0.0.0:8000`。
2. 在手机浏览器访问 `http://电脑局域网IP:8000/docs`；能打开接口文档后再测试 App。
3. 在 `mobile-uniapp` 创建 `.env.local`，将 API 地址改成当前电脑的局域网 IP：

```env
VITE_API_BASE=http://192.168.31.211:8000
```

4. 手机与电脑连接同一 Wi-Fi，并关闭可能改变网络路径的 VPN；Windows 防火墙需允许 TCP 8000 入站。
5. HBuilderX 选择“文件 → 打开目录”，直接打开 `mobile-uniapp`，不要新建一个空白 demo 工程。
6. 打开 `src/manifest.json`，申请 DCloud AppID，并配置 Android 包名、图标和签名。
7. 选择“发行 → 原生 App-云打包”，平台选择 Android；测试阶段可使用公共测试证书，正式发布必须使用自己的证书。
8. APK 安装后使用网站已有邮箱和密码登录；移动端与 Web 端共用后端、数据库和账号。

若打包出现 `There is insufficient memory for the Java Runtime Environment` 或错误码 `1455`，请关闭占用内存的软件，并在 Windows“高级系统设置 → 性能 → 高级 → 虚拟内存”中启用系统管理大小，重启电脑后重新打包。正式上线时必须将局域网 HTTP 地址替换为可公网访问的 HTTPS API 域名。

## Docker Compose 本地最小部署

项目根目录已经提供 `Dockerfile`、`docker-compose.yml`、`nginx.conf` 和针对 Python 3.13 锁定的
`requirements.txt`。当前 Compose 保持最小部署，只启动以下服务：

- `web`：FastAPI / Uvicorn 后端
- `db`：MySQL 8.0 业务数据库
- `postgres_db`：PostgreSQL 15，保存 LangGraph Checkpoint
- `redis`：验证码、缓存和分布式锁
- `nginx`：将本机 80 端口反向代理到 `web:8000`

### 1. 准备 Docker 环境变量

以现有 `.env` 为基础保留真实可用的 DeepSeek、JWT、邮件和支付宝配置，只修改 Docker 容器间连接地址。
不要把 `.env` 提交到 Git。至少确认以下配置存在：

```env
MYSQL_ROOT_PASSWORD=replace_with_your_mysql_root_password
POSTGRES_PASSWORD=replace_with_your_postgres_password

DB_URI=mysql+aiomysql://root:${MYSQL_ROOT_PASSWORD}@db:3306/ainame?charset=utf8mb4
LANGGRAPH_DB_URI=postgresql://postgres:${POSTGRES_PASSWORD}@postgres_db:5432/ai_name
REDIS_URL=redis://redis:6379/0

# 本机开发地址；正式上线后替换为 HTTPS 域名
FRONTEND_BASE_URL=http://127.0.0.1:5173
APP_BASE_URL=http://127.0.0.1:8000
ALIPAY_NOTIFY_URL=http://127.0.0.1:8000/pay/alipay_notify
ALIPAY_RETURN_URL=http://127.0.0.1:8000/pay/success
ALIPAY_DEBUG=true
```

代码读取的支付宝公钥变量名是 `ALIPAY_PUBLIC_KEY`，不是
`ALIPAY_ALIPAY_PUBLIC_KEY`。`ALIPAY_DEBUG=true` 仅适用于沙箱；切换正式网关时必须改为 `false`。
支付宝服务器无法回调 `127.0.0.1`，因此本机配置只能用于开发；完整异步通知测试需要公网 HTTPS 地址或安全的临时隧道。

### 2. 构建并启动

```powershell
docker compose config -q
docker compose up -d --build
docker compose ps
```

`docker compose config -q` 应无输出并以状态码 0 结束。启动后可访问：

- Nginx / API：`http://127.0.0.1/`
- Swagger UI：`http://127.0.0.1/docs`
- 直接访问后端（仅容器端口映射存在时）：`http://127.0.0.1:8000/docs`

当前 `web` 服务没有发布宿主机 8000 端口，因此以现有 Compose 配置为准，应通过 Nginx 的 80 端口访问。

### 3. 初始化数据库

容器健康后执行 MySQL 迁移和 PostgreSQL Checkpoint 初始化：

```powershell
docker compose exec web alembic upgrade head
docker compose exec web python init_pg_memory.py
```

### 4. 查看日志与停止服务

```powershell
docker compose logs -f web
docker compose down
```

`docker compose down` 不会删除命名卷中的数据库数据。只有明确需要清空本地数据时才使用
`docker compose down -v`。

### 当前最小部署限制

当前 Compose 有意不包含 RabbitMQ、`rag_worker` 和 Ollama，因此知识库上传后的异步解析、向量化与 RAG
检索暂不可用；其他不依赖这些服务的后端功能仍可继续开发。React 前端也未打包进 Nginx，需继续通过
`npm run dev` 在 `http://127.0.0.1:5173` 启动。

## 手动完整初始化

不使用 Docker Compose 时，首次部署请继续完成下面的完整初始化步骤。

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
python -m pip install -r requirements.txt
```

### 4. 创建 MySQL 数据库

```sql
CREATE DATABASE ai_name
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
```

### 5. 创建 PostgreSQL 记忆数据库

LangGraph 使用独立的 PostgreSQL 数据库保存 Checkpoint：

```sql
CREATE DATABASE ai_name;
```

PostgreSQL 连接地址通过 `.env` 中的 `LANGGRAPH_DB_URI` 统一配置，例如：

```text
postgresql://postgres:your_password@127.0.0.1:5432/ai_name
```

### 6. 配置环境变量

在项目根目录创建 `.env`：

```env
DB_URI=mysql+aiomysql://root:your_password@127.0.0.1:3306/ai_name?charset=utf8mb4
LANGGRAPH_DB_URI=postgresql://postgres:your_password@127.0.0.1:5432/ai_name
RABBITMQ_URL=amqp://your_user:your_password@127.0.0.1:5672/

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
REDIS_URL=redis://127.0.0.1:6379/0

# 阿里云百炼 / 通义万相 Logo 生成配置
DASHSCOPE_API_KEY=replace_with_your_dashscope_api_key
DASHSCOPE_IMAGE_API_URL=https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
WANXIANG_MODEL=wan2.6-t2i
APP_BASE_URL=http://127.0.0.1:8000

# 支付宝开放平台配置
ALIPAY_APP_ID=your_alipay_app_id
ALIPAY_SELLER_ID=your_alipay_seller_id
ALIPAY_APP_PRIVATE_KEY=your_app_private_key_without_header
ALIPAY_PUBLIC_KEY=your_alipay_public_key_without_header
ALIPAY_DEBUG=true  # 支付宝沙箱为 true，生产环境必须改为 false
ALIPAY_GATEWAY=your_alipay_gateway_url
ALIPAY_RETURN_URL=http://127.0.0.1:8000/pay/success
ALIPAY_NOTIFY_URL=https://your-public-domain.example.com/pay/alipay_notify
```

你可以用下面的命令生成一个 JWT 密钥：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 7. 执行 MySQL 数据库迁移

```bash
alembic upgrade head
```

如需启用管理员与 RBAC 管理接口，迁移完成后创建或提升首个管理员：

```bash
python scripts/create_admin.py admin@example.com --username 管理员
```

脚本会在终端安全询问初始密码；如果邮箱已存在，则直接为该用户分配管理员角色。

### 8. 初始化 PostgreSQL Checkpoint 表

首次运行或记忆数据库尚未初始化时执行：

```bash
python init_pg_memory.py
```

预期输出：

```text
✅ PostgreSQL 记忆持久化数据表创建成功！
```

### 9. 启动 RabbitMQ

确认 RabbitMQ 服务已启动，并确保 `.env` 中 `RABBITMQ_URL` 对应的用户有权访问目标 Virtual Host。知识库上传接口会将解析任务投递到持久化队列 `rag_document_queue`。

### 10. 启动 Redis

确认 Redis 正常运行：

```bash
redis-cli ping
```

预期返回：

```text
PONG
```

### 11. 准备本地向量模型

安装并启动 Ollama 后下载项目使用的 Embedding 模型：

```bash
ollama pull qwen3-embedding:4b
```

只有企业命名和知识库功能需要使用该模型。人名、宠物名仍可直接调用 DeepSeek 工作流。

### 12. 启动 RAG Worker

单独打开一个终端运行知识库任务消费者：

```bash
python rag_worker.py
```

Worker 会逐个处理队列中的文档，执行解析、切片、向量化并写入用户专属 Chroma Collection。

### 13. 启动后端服务

```bash
python run_server.py --reload
```

Windows 用户也可以直接运行：

```bat
start.bat
```

启动后可访问：

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 14. 安装并启动前端

新开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

Vite 默认在 `http://127.0.0.1:5173` 提供页面，并将 `/api/*` 代理到
`http://127.0.0.1:8000/*`。开发环境无需修改 FastAPI 的 CORS 配置。

### 15. 生产构建前端

```powershell
cd frontend
npm run build
```

构建产物会生成到 `frontend/dist/`。如果前后端使用不同域名部署，可复制
`frontend/.env.example` 为 `frontend/.env.local`，并配置：

```env
VITE_API_BASE=https://api.example.com
```

跨域部署时，还需要在 FastAPI 或反向代理中允许前端站点的 Origin。生产环境更推荐
通过 Nginx 将 `/api` 反向代理到 FastAPI，从而保留默认的同源配置。

## 前端页面与功能

| 页面 | 功能 |
| ---- | ---- |
| 首页 | 产品介绍、三类起名入口与使用流程 |
| 智能起名 | 生成 5 个候选名、连续反馈微调，并确认 1 个最终名称 |
| 专属知识库 | 上传 TXT/PDF 品牌资料，构建用户隔离的 RAG 知识库 |
| 品牌 Logo | 读取已选定的企业名称，设置风格并生成 Logo、查看原图 |
| 名称校验 | 校验域名、商标、企业和社交平台风险，并保存校验历史 |
| 品牌资产 | 根据最终企业名生成定位、Slogan、Logo 概念和域名矩阵 |
| 命名报告 | 汇总项目、候选轮次、最终选名、校验和品牌资产，生成 PDF |
| 专家服务 | 专家入驻、服务套餐、精批订单、交付报告、评价与结算 |
| 社区投票 | 发布候选名投票、投票、评论、举报与社区精选 |
| 开放平台 | 开发者账号、API Key、套餐额度、单次/批量命名和调用统计 |
| 邀请有礼 | 推广码、邀请关系、次数奖励与佣金记录 |
| 我的项目 | 查看项目轮次、候选名、最终选名、归档和恢复 |
| 我的订单 | 查看订单与交易流水，继续支付、同步状态或关闭订单 |
| 我的任务 | 查看异步任务进度和失败原因，并重试失败任务 |
| 我的次数 | 查看次数余额、累计使用和完整权益流水 |
| 套餐 | 查询上架套餐、创建订单并跳转支付宝收银台 |
| 用户中心 | 资料、头像、密码、登录设备、安全记录与业务数据总览 |
| 运营后台 | 用户、权限、次数、套餐、订单、项目、报告、知识库、任务及业务模块管理 |
| 登录/注册入口 | 未登录时覆盖全站，支持邮箱验证码注册、登录和 Token 自动刷新 |

## 本地功能验收

### 1. 启动完整开发环境

确认 MySQL、PostgreSQL、Redis 和 RabbitMQ 已启动，并在项目根目录执行：

```powershell
conda activate fastapi-env
alembic upgrade head
python init_pg_memory.py
python run_server.py --reload
```

知识库上传和异步解析还需要第三个终端：

```powershell
conda activate fastapi-env
cd D:\Code\1\ai_name
python rag_worker.py
```

前端使用另一个终端：

```powershell
cd D:\Code\1\ai_name\frontend
npm install
npm run dev
```

打开以下地址：

- 用户前端：http://127.0.0.1:5173
- Swagger 接口调试：http://127.0.0.1:8000/docs
- ReDoc 接口文档：http://127.0.0.1:8000/redoc

### 2. 准备测试账号

普通用户可以在前端注册。若邮件服务尚未配置，可先使用 Swagger 或 Redis/测试环境完成验证码流程。管理员账号在迁移完成后创建：

```powershell
python scripts/create_admin.py admin@example.com --username 管理员
```

脚本会在终端询问密码。管理员登录后，页面导航会出现“运营后台”。

### 3. 推荐手工验收顺序

1. 注册、登录、退出，再测试密码找回、资料修改和登录设备撤销。
2. 进入“智能起名”，分别测试人名、企业名、宠物名，提交反馈生成第二轮，并确认最终名称。
3. 在“我的项目”确认轮次和最终选名已经保存，再测试归档与恢复。
4. 对企业最终名称执行“名称校验”，然后生成“品牌资产”和“品牌 Logo”。
5. 进入“命名报告”生成 PDF，下载后检查中文字体、分页、表格和品牌资产章节。
6. 上传 TXT/PDF 到“专属知识库”，同时观察“我的任务”和 Worker 终端，确认最终状态为已完成。
7. 在“套餐”创建测试订单；支付宝功能必须使用沙箱配置，避免在开发环境产生真实交易。
8. 测试专家入驻、管理员审核、专家套餐、用户下单、专家交付、用户评价和管理员结算。
9. 发布社区投票，用另一个用户投票、评论和举报，再由管理员精选或处理举报。
10. 开通开发者账号，创建 API Key、领取体验额度，并按页面 curl 示例测试单次和批量命名。
11. 复制“邀请有礼”的注册链接，使用新浏览器或无痕窗口注册，检查双方次数奖励和支付佣金记录。
12. 管理员依次检查用户、角色审计、次数、套餐、订单详情、项目、报告、知识库、任务及各业务后台。

### 4. 自动化回归

前端测试与生产构建：

```powershell
cd D:\Code\1\ai_name\frontend
npm test
npm run build
```

后端编译、迁移状态和全部集成测试：

```powershell
cd D:\Code\1\ai_name
python -m compileall -q .
alembic current
alembic heads
python -m unittest tests.test_auth_stage_integration tests.test_community_stage_integration tests.test_developer_stage_integration tests.test_expert_stage_integration tests.test_growth_stage_integration
```

使用现有普通用户逐项检查用户页面接口，并使用自动清理的隔离管理员检查后台页面接口：

```powershell
python scripts/audit_page_apis.py --email 你的普通用户邮箱
```

脚本不会修改目标用户的密码、角色或业务数据；临时设备会话与隔离管理员会在结束时删除。

集成测试会写入本地测试数据并在结束时清理；请勿让测试环境指向生产数据库。

## 接口说明

### 认证相关

| 方法 | 路径                | 说明                                 |
| ---- | ------------------- | ------------------------------------ |
| GET  | /auth/code          | 发送注册验证码                       |
| POST | /auth/register      | 用户注册                             |
| POST | /auth/login         | 登录并获取双 Token                   |
| GET  | /auth/verify-access | 验证 Access Token                    |
| POST | /auth/refresh       | 轮换 Refresh Token 并换取新双 Token |
| POST | /auth/logout        | 撤销当前设备会话并退出登录 |
| POST | /auth/password-reset/code | 发送密码重置验证码 |
| POST | /auth/password-reset/confirm | 使用验证码重置密码 |

### 用户中心与权限

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| GET | /users/me | 查询当前用户资料与角色 |
| GET | /users/me/dashboard | 汇总次数、流水、项目、订单、知识库和最近报告 |
| PATCH | /users/me | 修改用户名或头像地址 |
| POST | /users/me/avatar | 上传 JPG/PNG/WebP 头像，最大 2MB |
| POST | /users/me/password | 修改密码并撤销全部旧会话 |
| GET | /users/me/devices | 查询登录设备 |
| DELETE | /users/me/devices/{device_id} | 撤销指定设备登录 |
| GET | /users/me/login-records | 查询最近登录记录 |
| GET | /admin/users | 按 RBAC 权限查询用户 |
| PATCH | /admin/users/{user_id}/status | 冻结或解冻账号 |
| PUT | /admin/users/{user_id}/roles | 分配用户角色 |
| GET/POST | /admin/roles | 查询或创建角色 |
| GET | /admin/permissions | 查询权限列表 |
| PUT | /admin/roles/{role_code}/permissions | 配置角色权限 |
| GET | /admin/audit-logs | 查询管理员操作日志 |
| GET | /admin/dashboard | 查询平台核心运营数据看板 |
| GET | /admin/projects | 查询和筛选全平台命名项目 |

### 起名与积分相关

| 方法 | 路径            | 说明                     |
| ---- | --------------- | ------------------------ |
| POST | /name/generate  | 首次生成名字并返回 `thread_id` |
| POST | /name/feedback  | 使用 `thread_id` 提交反馈并微调名字 |
| POST | /name/select    | 从当前会话最新候选中选定最终名称 |
| GET  | /name/selections/{selection_id} | 查询当前用户的最终名称及 Logo 状态 |
| GET  | /credit/balance | 查询当前用户剩余起名次数 |
| GET  | /credit/account | 查询余额、累计使用和累计充值 |
| GET  | /credit/logs | 查询当前用户次数流水 |
| GET  | /admin/credits | 管理员查询用户次数账户 |
| POST | /admin/users/{user_id}/credits | 管理员幂等调整用户次数并写审计日志 |

### 套餐相关

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| GET | /package/list | 按后台排序查询所有上架套餐 |
| GET | /admin/packages | 管理员查询全部套餐和上下架状态 |
| POST | /admin/packages | 新增套餐 |
| PATCH | /admin/packages/{package_id} | 修改套餐名称、说明、价格、次数和排序 |
| POST | /admin/packages/{package_id}/status | 上架或下架套餐 |
| PUT | /admin/packages/sort | 批量调整套餐顺序 |
| DELETE | /admin/packages/{package_id} | 删除无订单套餐；已有订单时要求下架 |

### 命名项目相关

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| POST | /projects | 创建项目草稿并保存命名条件 |
| GET | /projects | 查询项目历史，支持按状态筛选 |
| GET | /projects/{project_id} | 查询项目、候选轮次和最终选名详情 |
| PATCH | /projects/{project_id} | 修改项目名称或草稿命名条件 |
| POST | /projects/{project_id}/archive | 归档项目 |
| POST | /projects/{project_id}/restore | 恢复项目并还原业务状态 |

### 知识库相关

| 方法 | 路径 | 鉴权 | 说明 |
| ---- | ---- | ---- | ---- |
| POST | /knowledge/upload | 是 | 上传 TXT/PDF 文件、建立记录并投递 RabbitMQ |
| GET | /knowledge/files | 是 | 查询当前用户的文件与处理状态 |
| GET | /knowledge/files/{file_id} | 是 | 查询当前用户的文件详情 |
| POST | /knowledge/files/{file_id}/reprocess | 是 | 重新处理失败或已完成文件 |
| DELETE | /knowledge/files/{file_id} | 是 | 删除源文件及其向量数据 |
| GET | /admin/knowledge/files | 是（管理员） | 查询和筛选全站知识库文件 |
| POST | /admin/knowledge/files/{file_id}/reprocess | 是（管理员） | 管理员重新处理文件 |
| DELETE | /admin/knowledge/files/{file_id} | 是（管理员） | 管理员删除文件并记录审计日志 |

### Logo 相关

| 方法 | 路径            | 鉴权 | 说明                               |
| ---- | --------------- | ---- | ---------------------------------- |
| POST | /logos/generate | 是   | 为当前用户已选定的企业名称生成 Logo |

### 异步任务相关

| 方法 | 路径 | 鉴权 | 说明 |
| ---- | ---- | ---- | ---- |
| GET | /tasks | 是 | 查询当前用户最近的异步任务，可按状态筛选 |
| GET | /tasks/{task_id} | 是 | 查询任务进度、尝试次数和失败原因 |
| POST | /tasks/{task_id}/retry | 是 | 人工重试自己的失败或已取消任务 |
| GET | /admin/tasks | 是（管理员） | 查询全站任务，可按状态和任务类型筛选 |
| POST | /admin/tasks/{task_id}/retry | 是（管理员） | 管理员重试任务并记录审计日志 |
| POST | /admin/tasks/{task_id}/cancel | 是（管理员） | 取消排队任务并同步业务状态 |

### 名称校验相关

| 方法 | 路径 | 鉴权 | 说明 |
| ---- | ---- | ---- | ---- |
| GET | /name/selections | 是 | 查询当前用户的最终选名 |
| POST | /validations | 是 | 对最终企业名称执行综合风险校验 |
| GET | /validations | 是 | 查询自己的校验历史，可按最终选名筛选 |
| GET | /validations/{validation_id} | 是 | 查询校验报告详情 |
| GET | /admin/validations | 是（管理员） | 按状态或风险等级查询平台校验记录 |

名称校验使用 IANA 的 RDAP Bootstrap Registry 发现各域名后缀的权威 RDAP 服务。商标和企业数据通常需要合规商业数据源，后端通过以下环境变量接入统一 JSON API：

```env
TRADEMARK_CHECK_API_URL=
TRADEMARK_CHECK_API_TOKEN=
COMPANY_CHECK_API_URL=
COMPANY_CHECK_API_TOKEN=
SOCIAL_PROFILE_TEMPLATES={"微博":"https://example.com/{username}"}
```

商标和企业 API 接收 `{"name":"待查询名称"}`，返回 `{"matches":[{"name":"近似名称","similarity":0.85}]}`。未配置、超时或返回异常时，报告会降低覆盖率并显示“数据不足”，不会误判为低风险。社交平台模板仅应填写允许自动查询且能以 HTTP 404 表示不存在的合规接口。

### 品牌价值资产相关

| 方法 | 路径 | 鉴权 | 说明 |
| ---- | ---- | ---- | ---- |
| POST | /brand-assets | 是 | 为最终企业名称生成并保存一个品牌资产版本 |
| GET | /brand-assets | 是 | 查询自己的品牌资产，可按最终选名筛选 |
| GET | /brand-assets/{asset_id} | 是 | 查询自己的品牌资产详情 |
| GET | /admin/brand-assets | 是（管理员） | 查询平台品牌资产生成记录 |

创建时提交 `selected_name_id`、唯一的 `client_request_id`，并可选提交 `validation_id` 和品牌简报 `brief`。未指定校验记录时，系统自动使用该最终名称的最新校验；若没有校验记录，仍可生成策略内容，但域名矩阵保持为空并明确提示先校验。

品牌资产包含品牌定位说明、3～6 条 Slogan、2～4 个 Logo 概念方向、品牌色/字体/图像/版式建议、域名矩阵和风险行动清单。请求使用用户级请求锁与选名级生成锁，重复提交不会重复调用 AI 或产生重复版本。名称校验数据以快照保存，后续仍可追溯生成时依据。风险内容不构成法律意见、商标核准或域名注册保证。

### PDF 命名报告相关

| 方法 | 路径 | 鉴权 | 说明 |
| ---- | ---- | ---- | ---- |
| POST | /reports | 是 | 为自己的命名项目生成 PDF 报告；请求支持幂等 |
| GET | /reports | 是 | 查询自己的报告中心 |
| GET | /reports/{report_id} | 是 | 查询自己的报告详情 |
| GET | /reports/{report_id}/download | 是 | 鉴权下载自己的 PDF 报告 |
| GET | /admin/reports | 是（管理员） | 查询平台报告记录 |
| GET | /admin/reports/{report_id}/download | 是（管理员） | 管理员鉴权下载报告 |

报告绑定当前用户自己的项目和最终选名，自动采用最新名称校验与品牌资产，并把生成依据保存为数据库快照。PDF 文件写入 `output/pdf/`，不挂载为公开静态资源；下载接口校验用户归属或 `reports.manage` 权限，并返回文件摘要。生成失败时不写入报告记录，也不会遗留半成品文件。

### 套餐与支付相关

| 方法 | 路径                    | 鉴权 | 说明                         |
| ---- | ----------------------- | ---- | ---------------------------- |
| GET  | /package/list           | 否   | 查询当前已上架的套餐         |
| POST | /pay/create_order       | 是   | 创建订单并返回支付宝支付地址 |
| GET  | /pay/order/{order_no}   | 是   | 查询当前用户的订单状态       |
| GET  | /pay/orders | 是 | 查询当前用户订单列表 |
| GET  | /pay/orders/{order_no}/detail | 是 | 查询订单详情和支付/退款流水 |
| POST | /pay/orders/{order_no}/pay | 是 | 为待支付订单重新生成支付地址 |
| POST | /pay/orders/{order_no}/sync | 是 | 主动向支付宝同步支付结果并幂等到账 |
| POST | /pay/orders/{order_no}/close | 是 | 关闭当前用户的待支付订单 |
| GET  | /pay/success            | 否   | 支付宝浏览器同步回跳地址     |
| POST | /pay/alipay_notify      | 否   | 支付宝服务器异步通知地址     |
| GET | /admin/orders | 是（管理员） | 查询和筛选平台订单 |
| GET | /admin/orders/{order_no} | 是（管理员） | 查询订单与交易流水详情 |
| POST | /admin/orders/{order_no}/close | 是（管理员） | 管理员关闭待支付订单 |
| POST | /admin/orders/{order_no}/refund | 是（管理员） | 幂等发起支付宝退款并回收次数权益 |

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
POST http://127.0.0.1:8000/name/generate
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
  "thread_id": "7e30ebcc-50d8-41aa-aea7-834767036ec4",
  "names": [
    {
      "name": "候选名字",
      "reference": "出处",
      "moral": "寓意",
      "domain": "example.com",
      "domain_status": "✅ 未注册 (可买)"
    }
  ]
}
```

`thread_id` 对应 PostgreSQL 中保存的 LangGraph Checkpoint。后续微调必须原样传回：

```http
POST http://127.0.0.1:8000/name/feedback
Content-Type: application/json
Authorization: Bearer your_access_token

{
  "thread_id": "7e30ebcc-50d8-41aa-aea7-834767036ec4",
  "category": "人名",
  "feedback": "保留清雅的风格，换成带水字旁的字"
}
```

### 选定最终名称

生成或微调完成后，从最新 5 个候选名中提交一个名称。后端会从 Checkpoint
中重新核对候选列表和用户归属，不接受任意名称：

```http
POST http://127.0.0.1:8000/name/select
Content-Type: application/json
Authorization: Bearer your_access_token

{
  "thread_id": "7e30ebcc-50d8-41aa-aea7-834767036ec4",
  "name": "青衍科技"
}
```

响应中的 `id` 是最终选择记录 ID。`can_generate_logo` 只有在类别为企业名时才是
`true`：

```json
{
  "id": 12,
  "thread_id": "7e30ebcc-50d8-41aa-aea7-834767036ec4",
  "category": "企业名",
  "name": "青衍科技",
  "reference": "品牌创意来源",
  "moral": "寓意清新生长与科技延展",
  "logo_prompt": "",
  "logo_url": "",
  "logo_status": "not_generated",
  "can_generate_logo": true
}
```

### 上传用户知识库

仅支持不超过 10MB 的 TXT 和 PDF 文件。服务端会校验扩展名和 PDF 文件头，并生成随机存储文件名，避免客户端文件名造成路径穿越或覆盖。接口保存文件后会向 RabbitMQ 投递任务，文件解析和向量化由 `rag_worker.py` 完成。接口返回成功后需等待 Worker 处理完毕，再发起企业命名请求。

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

### 生成企业 Logo

```http
POST http://127.0.0.1:8000/logos/generate
Content-Type: application/json
Authorization: Bearer your_access_token

{
  "selection_id": 12,
  "style_feedback": "极简、科技感、使用青绿色"
}
```

Logo 接口不会接收任意 `company_name`，而是根据 `selection_id` 读取当前用户已经
选定的企业名称。生成成功后，响应中的 `logo_url` 指向 `/static/logos/` 下的图片，
结果也会保存到 `selected_name` 表。请确保 `APP_BASE_URL` 是客户端能够访问的后端地址。

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

### 专家服务

第十三阶段已实现完整的专家服务闭环：

- 用户提交专家入驻资料，管理员审核通过后自动授予 `expert` 角色。
- 认证专家可发布、上下架服务套餐，并处理接单与文字报告交付。
- 用户可浏览在售套餐、关联自己的命名项目下单、查看交付并评价。
- 订单完成后按订单金额自动生成结算记录，当前平台服务费率为 10%。
- 管理员可查看专家申请、全部精批订单与结算记录，并确认线下结算。
- 下单使用 `client_request_id` 保证幂等；订单、交付、评价和结算均有严格状态校验与用户隔离。

专家订单当前采用平台内订单与人工结算流程，尚未接入支付宝自动收款及自动分账。相关入口为：

- 用户端：`#/experts`
- 专家端：`#/expert-workspace`
- 运营后台：`#/admin-experts`

### 社区众包

第十四阶段已实现基于现有命名项目的社区共创闭环：

- 用户从本人项目最新一轮候选中选择 2–12 个名称发布投票。
- 发布时保存名称、出处和寓意快照，项目后续修改不会影响社区内容。
- 社区用户可浏览候选、投票或改票，并查看实时票数与占比。
- 开放投票支持评论互动，发布者可主动结束投票；结束后禁止继续投票和评论。
- 用户可举报投票或评论，不能举报自己的内容，同一目标重复举报保持幂等。
- 运营人员可维护社区精选，驳回举报或隐藏违规投票、评论，操作写入审计日志。
- 社区接口不会公开项目条件、线程 ID 或其他项目私有信息。

相关前端入口：

- 社区广场：`#/community`
- 发布投票：`#/community-publish`
- 运营后台：`#/admin-community`

### B 端开放平台

第十五阶段已实现开发者接入、凭证安全、API 调用和额度计费闭环：

- 登录用户可开通开发者账号，并创建最多 10 个有效 API Key。
- Key 使用高熵随机值，服务端只保存 SHA-256 摘要与前缀；完整明文仅创建时返回一次。
- 开放接口通过 `X-API-Key` 鉴权，支持单次命名与最多 10 项的批量命名。
- 调用复用主站正式分类工作流，支持人名、企业名和宠物名；完成后清理临时会话状态。
- 每个任务按一个调用单位计费，调用前原子预扣，模型失败自动返还。
- 同一 Key 的 `request_id` 保证幂等；跨端点复用会返回 409，避免响应和账单混淆。
- 控制台展示套餐余额、调用状态、耗时和汇总统计。
- 免费体验包可自助领取一次；付费套餐采用管理员合同授予，未伪造线上付款流程。
- 管理员可创建 API 套餐、授予额度、停用开发者；停用时撤销该账号全部有效 Key。

开放接口：

```http
POST /openapi/v1/names/generate
X-API-Key: qmk_live_xxx
Content-Type: application/json

{
  "request_id": "unique-request-id",
  "category": "企业名",
  "surname": "",
  "gender": "不限",
  "length": "两字",
  "other": "科技协作品牌",
  "exclude": []
}
```

- 批量命名：`POST /openapi/v1/names/batch`
- 开发者控制台：`#/developers`
- 运营后台：`#/admin-developers`

### 增长与分销

第十六阶段已实现一层直接邀请与推广核算闭环：

- 每个用户可生成唯一推广码和邀请链接。
- 注册页支持自动带入或手动填写邀请码，邀请关系注册后不可改绑。
- 无效邀请码会使用户创建、默认赠送和邀请绑定整体回滚，不产生半成品账户。
- 活动可分别配置邀请人、受邀人次数奖励，以及最高 50% 的一层订单佣金比例。
- 邀请关系、双方奖励和次数流水在同一事务内写入，并使用唯一约束和业务键防止重复奖励。
- 受邀用户订单仅在首次支付成功时生成佣金，支付宝重复通知不会重复计算。
- 退款成功会自动冲销对应佣金；退款失败恢复订单时不会错误冲销。
- 用户增长中心展示推广码、邀请人数、奖励流水及佣金记录。
- 运营后台支持活动创建、启停和全平台佣金查询，操作写入审计日志。

当前仅维护佣金内部核算记录，不提供提现或自动出款。真实结算上线前必须接入实名、税务、反作弊与支付机构合规分账能力。

- 用户增长中心：`#/growth`
- 邀请注册链接：`#/register/{推广码}`
- 运营后台：`#/admin-growth`

## 业务阶段完成后的上线收尾

规划中的用户中心、运营后台、专家服务、社区众包、B 端开放平台、增长与分销六大扩展模块均已实现。正式上线前仍需完成：

- 全站安全审计、依赖漏洞扫描、密钥轮换和敏感信息检查。
- AI、数据库、Redis、RabbitMQ 和开放 API 的并发压测与容量规划。
- 专家服务真实收款与分账、推广佣金实名提现及税务合规。
- 生产域名、HTTPS、反向代理、CORS、对象存储和 CDN 配置。
- 日志聚合、指标监控、异常告警、链路追踪和运营审计留存。
- MySQL/PostgreSQL/Redis/对象文件的备份、恢复演练和灾难恢复方案。
- 隐私政策、用户协议、社区规范、专家协议及开放平台服务协议。
- 正式环境端到端验收、灰度发布、回滚预案与上线检查清单。

## 备注

- 注册成功后会自动赠送 3 次起名机会。
- 每次成功起名后会扣除 1 次机会；扣次与失败返还均使用业务操作号防止重复记账。
- 企业命名会优先检索当前用户的专属知识库，不同用户的数据使用独立 Chroma Collection 隔离。
- 企业候选名会通过 Verisign WHOIS 服务查询 `.com` 域名状态；运行环境需允许访问 TCP 43 端口。
- 知识库上传依赖 RabbitMQ 和独立运行的 `rag_worker.py`，仅启动 FastAPI 不会消费解析任务。
- Logo 接口要求登录，并且只允许操作当前用户已选定的企业名称。
- `/pay/alipay_notify` 必须能够被支付宝服务器公网访问，不能添加 Bearer Token 鉴权。
- 支付入账以验签、订单金额和订单状态为依据；异步通知是生产环境的主要入账方式。
- 执行 `alembic upgrade head` 会创建最终名称和命名项目相关表；迁移不会自动插入套餐数据，使用支付接口前需先在 `package` 表中添加上架套餐。
- `.env`、`uploads/`、`chroma_rag_db/`、`static/logos/` 和 Python 缓存均已加入 Git 忽略规则。

## 故障排查

### `RuntimeError: no running event loop`

#### 问题现象

Uvicorn 启动并导入 `core/workflow.py` 时出现以下错误之一：

```text
AsyncConnectionPool open with no running loop
RuntimeError: no running event loop
```

报错可能发生在创建 `AsyncConnectionPool` 时，也可能发生在创建 `AsyncPostgresSaver` 时。

#### 根本原因

Python 导入模块时，Uvicorn 的异步事件循环尚未启动。以下对象如果在 `workflow.py` 模块顶层完成初始化，就会过早访问事件循环：

```python
connection_pool = AsyncConnectionPool(DB_URI)
memory = AsyncPostgresSaver(connection_pool)
naming_graph = workflow.compile(checkpointer=memory)
```

仅给连接池增加 `open=False` 还不够。它可以避免连接池在导入时打开，但 `AsyncPostgresSaver` 的构造函数本身也会调用 `asyncio.get_running_loop()`，因此 Saver 创建和 Graph 编译同样必须延后。

#### 解决方式

当前项目采用 FastAPI lifespan 管理完整的工作流生命周期：

1. 导入 `workflow.py` 时，只创建带有 `open=False` 的连接池对象。
2. 将 `memory` 和 `naming_graph` 初始设置为 `None`。
3. Uvicorn 建立事件循环后，lifespan 调用 `start_naming_memory()`。
4. 在异步上下文中依次打开连接池、创建 `AsyncPostgresSaver`、编译工作流。
5. 服务关闭时，lifespan 调用 `stop_naming_memory()` 清理工作流并关闭连接池。
6. `generate_names_v2()` 和 `feedback_names()` 在调用图之前检查工作流是否已经初始化。

正确的启动顺序如下：

```text
导入 workflow.py
    ↓
创建未打开的 AsyncConnectionPool
    ↓
Uvicorn 建立事件循环
    ↓
FastAPI lifespan 启动
    ↓
打开连接池并等待连接就绪
    ↓
创建 AsyncPostgresSaver
    ↓
编译 naming_graph
    ↓
开始处理请求
```

相关实现位于：

- `core/workflow.py`：`start_naming_memory()`、`stop_naming_memory()`
- `main.py`：`lifespan()`
- `run_server.py`：Windows 下在 Uvicorn 创建事件循环前启用 Selector loop，兼容异步 Psycopg

Windows 下不要直接运行 `uvicorn main:app`。Python 默认的 Proactor loop 与异步 Psycopg 不兼容，应使用 `python run_server.py`；Linux 和 macOS 也可以统一使用该入口。

如果修复后变成 PostgreSQL 连接失败，请确认：

- PostgreSQL 服务已经启动。
- `.env` 中已正确配置 `LANGGRAPH_DB_URI`。
- `ai_name` 数据库已经创建。
- 已执行 `python init_pg_memory.py` 初始化 Checkpoint 表。
- 已安装 `langgraph-checkpoint-postgres` 和 `psycopg[binary,pool]`。

## 后续可扩展方向

- 将上传文件和向量数据库迁移到对象存储与独立向量服务
- 扩展 Compose，加入 RabbitMQ、RAG Worker、Ollama 与前端静态资源构建

## 阶段开发与自动检查

每个后续阶段固定执行以下流程，通过全量回归后才进入下一阶段：

```text
开始前基线检查 → 功能开发 → 小范围测试 → 完整 Bug 检查
→ 修复问题 → 全量回归 → 更新 README 与路线图 → 下一阶段
```

当前数据库迁移版本：`n31e7a50b4d9`（增长活动、推广码、邀请关系、奖励与佣金记录）。

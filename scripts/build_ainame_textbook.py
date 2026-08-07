from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs" / "ainame_textbook"
PDF_PATH = OUT_DIR / "AINAME项目源码完全解析教材.pdf"

FONT_CN = Path(r"C:\Windows\Fonts\simhei.ttf")
FONT_CODE = Path(r"C:\Windows\Fonts\consola.ttf")
FONT_CODE_BOLD = Path(r"C:\Windows\Fonts\consolab.ttf")

PAGE_W, PAGE_H = A4
MM = 72 / 25.4

NAVY = HexColor("#102A43")
BLUE = HexColor("#0B74DE")
CYAN = HexColor("#17A2B8")
INK = HexColor("#243B53")
MUTED = HexColor("#627D98")
PAPER = HexColor("#F6F9FC")
CARD = white
LINE = HexColor("#D9E2EC")
GREEN = HexColor("#2F855A")
AMBER = HexColor("#C05621")
RED = HexColor("#C53030")


def mm(value: float) -> float:
    return value * MM


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("CN", str(FONT_CN)))
    pdfmetrics.registerFont(TTFont("CNB", str(FONT_CN)))
    pdfmetrics.registerFont(TTFont("Code", str(FONT_CODE)))
    pdfmetrics.registerFont(TTFont("CodeB", str(FONT_CODE_BOLD)))


def source_files() -> list[Path]:
    ignored = {"output", "tmp", "scripts", "uploads", ".git", "__pycache__"}
    allowed = {".py", ".ini", ".mako", ".txt", ".md", ".bat", ".http", ""}
    result = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in ignored for part in path.relative_to(ROOT).parts):
            continue
        # Never embed local secrets or VCS-only metadata in the deliverable.
        if path.name in {".env", ".gitignore"}:
            continue
        if path.suffix.lower() in allowed:
            result.append(path)
    return sorted(result, key=lambda p: p.relative_to(ROOT).as_posix().lower())


def read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def wrap_text(text: str, font: str, size: float, width: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for char in paragraph:
            candidate = current + char
            if pdfmetrics.stringWidth(candidate, font, size) <= width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = char
        if current:
            lines.append(current)
    return lines


def draw_wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float,
                 font: str = "CN", size: float = 9.2, leading: float = 14,
                 color: Color = INK, max_lines: int | None = None) -> float:
    c.setFont(font, size)
    c.setFillColor(color)
    lines = wrap_text(text, font, size, width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:-1] + "…"
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def draw_header(c: canvas.Canvas, page_no: int, chapter: str, title: str, lead: str) -> float:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(BLUE)
    c.rect(0, PAGE_H - mm(5), PAGE_W, mm(5), fill=1, stroke=0)
    c.setFont("CN", 8)
    c.setFillColor(BLUE)
    c.drawString(mm(16), PAGE_H - mm(15), chapter)
    c.setFont("CNB", 21)
    c.setFillColor(NAVY)
    c.drawString(mm(16), PAGE_H - mm(27), title)
    y = PAGE_H - mm(37)
    y = draw_wrapped(c, lead, mm(16), y, PAGE_W - mm(32), size=9.5, leading=13, color=MUTED, max_lines=3)
    c.setStrokeColor(LINE)
    c.line(mm(16), y - mm(2), PAGE_W - mm(16), y - mm(2))
    return y - mm(8)


def draw_footer(c: canvas.Canvas, page_no: int) -> None:
    c.setStrokeColor(LINE)
    c.line(mm(16), mm(13), PAGE_W - mm(16), mm(13))
    c.setFont("CN", 7.5)
    c.setFillColor(MUTED)
    c.drawString(mm(16), mm(8), "AINAME 项目源码完全解析教材 · 源码快照 2026-08-05")
    c.drawRightString(PAGE_W - mm(16), mm(8), f"{page_no:03d} / 100")


def draw_card(c: canvas.Canvas, x: float, y_top: float, w: float, title: str,
              body: str, accent: Color = BLUE, height: float = mm(37)) -> float:
    y = y_top - height
    c.setFillColor(CARD)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, height, mm(2.5), fill=1, stroke=1)
    c.setFillColor(accent)
    c.roundRect(x, y, mm(2.2), height, mm(1), fill=1, stroke=0)
    c.setFont("CNB", 10.5)
    c.setFillColor(NAVY)
    c.drawString(x + mm(6), y_top - mm(8), title)
    draw_wrapped(c, body, x + mm(6), y_top - mm(15), w - mm(12), size=8.3,
                 leading=11.2, color=INK, max_lines=7)
    return y - mm(4)


@dataclass
class Lesson:
    title: str
    lead: str
    sections: list[tuple[str, str]]
    diagram: str | None = None


INTRO = [
    Lesson("如何使用这本教材", "把它当作交接手册、课程讲义和审计底稿的合体：先建立地图，再沿真实请求链阅读。", [
        ("三遍阅读法", "第一遍看第 3-8 页建立全局地图；第二遍按业务链跳读文件精读页；第三遍回到源码，逐个断点验证。"),
        ("证据约定", "所有结论以当前 ai_name 工作区为准。文件页给出真实行数、导入、符号和代码截图；审计结论区分事实、推断与建议。"),
        ("学习产出", "读完后应能解释请求如何进入 FastAPI、如何鉴权和计费、工作流怎样选择专家、RAG 与支付怎样落地。"),
    ]),
    Lesson("项目知识思维导图", "AINAME 的中心不是单次模型调用，而是一组围绕命名产品的业务能力。", [
        ("产品域", "身份、起名、反馈微调、私有知识库、域名可用性、Logo、套餐与支付。"),
        ("平台域", "HTTP/JSON、依赖注入、异步 I/O、数据库事务、消息队列、静态文件与第三方 API。"),
        ("AI 域", "DeepSeek 结构化输出、LangGraph 状态机、PostgreSQL Checkpoint、Embedding、Chroma 相似度检索。"),
    ], "mindmap"),
    Lesson("项目是什么", "这是一个面向中文命名场景的 FastAPI 后端：把 AI 创作变成可注册、可计费、可追踪、可迭代的产品服务。", [
        ("解决的问题", "普通聊天模型难以保持结构、上下文和商业规则。项目用 Schema 约束输出，用 Checkpoint 保存轮次，用 RAG 注入用户私有规范。"),
        ("用户场景", "人名强调文化出处，企业名叠加知识库与 .com 域名检查，宠物名强调个性；企业结果还能继续生成 Logo。"),
        ("商业闭环", "注册赠送次数；成功生成扣减一次；套餐创建订单；支付宝回调入账并写流水。"),
    ]),
    Lesson("系统边界与外部服务", "源码本身只是协调层，真正运行还依赖数据库、中间件、本地模型和多家外部服务。", [
        ("持久化", "SQLAlchemy 业务库保存用户、套餐、订单和次数；LangGraph PostgreSQL 保存工作流状态；Chroma 保存向量。"),
        ("基础设施", "Redis 保存 5 分钟验证码，RabbitMQ 解耦文件向量化，Ollama 提供本地 qwen3-embedding:4b。"),
        ("外部网络", "DeepSeek 生成名称，DashScope/万相生成图像，支付宝处理付款，SMTP 发邮件，Verisign WHOIS 查域名。"),
    ], "context"),
    Lesson("一次请求的完整生命周期", "从 TCP 连接到数据库提交，每个 await 都是一次把控制权交回事件循环的机会。", [
        ("入口", "Uvicorn 解析 HTTP，FastAPI 匹配方法与路径，Pydantic 校验 JSON，并解析 Depends 依赖。"),
        ("业务", "路由只做编排：鉴权、余额检查、调用工作流或仓储。核心状态变化由事务包裹。"),
        ("出口", "返回对象经 response_model 序列化成 JSON；HTTP 异常转成状态码和 detail；未处理异常成为 500。"),
    ], "request"),
    Lesson("分层架构总览", "代码采用轻量分层：Router 面向协议，Core 面向能力，Repository 面向数据，Model/Schema 分别描述存储与边界。", [
        ("调用方向", "main → routers → core/repository → models/外部服务。schemas 同时服务输入校验、模型结构化输出和响应序列化。"),
        ("设计收益", "路由不直接拼 SQL；模型调用集中在 workflow；外部服务封装在 tools。这样便于测试和替换。"),
        ("当前缺口", "没有独立 service 层和统一配置对象；部分路由文件重复导入、同步调用混入异步请求，边界仍可收紧。"),
    ], "layers"),
    Lesson("目录结构导航", "根目录共 50 个纳入分析的源码/配置/说明文件；没有 requirements 或 pyproject，这是可复现性的明显缺口。", [
        ("核心目录", "core/：AI、鉴权、支付、邮件、RAG、Redis；routers/：HTTP API；repository/：数据库用例；models/：ORM；schemas/：Pydantic。"),
        ("迁移与运行", "alembicdb/ 维护业务表迁移；main.py 创建应用；rag_worker.py 消费队列；init_pg_memory.py 初始化 Checkpoint。"),
        ("验证材料", "test.http 与 test_name.http 是手工请求脚本；README.md 是运行说明；company_rules.txt 是 RAG 示例语料。"),
    ], "tree"),
    Lesson("如何做逐行源码阅读", "逐行理解不是逐字翻译，而是回答：解释器何时执行、状态怎样变化、删除后谁会坏、边界条件在哪里。", [
        ("导入行", "判断导入发生在模块加载期还是函数调用期；模块级对象会在每个进程启动时创建一次，并可能使启动因缺少环境变量而失败。"),
        ("定义行", "class/def 执行时创建对象但不运行函数体；装饰器立即应用；FastAPI 路由装饰器把函数登记进路由表。"),
        ("执行行", "沿参数 → 分支 → await → 副作用 → 返回值追踪。对事务、文件写入、外部请求尤其要标出失败窗口。"),
    ]),
]


CONCEPTS = [
    ("Python 模块与 import", "模块是被执行一次并缓存于 sys.modules 的对象。AINAME 导入 main 时会连带导入路由、模型与 workflow；模块级环境检查因此属于启动关键路径。", "删除 import 会在名称首次使用时报 NameError；循环导入会暴露半初始化模块。models/__init__.py 尾部导入模型是为了让 Base.metadata 看见所有表。"),
    ("类、对象与内存", "class 语句创建类对象；调用类产生实例；self 指向实例。User、Repository、Pydantic Schema 和 ORM Model 都是类，但承担不同职责。", "User 的 password setter 把明文转为哈希；Repository 持有 AsyncSession；Schema 通常是短生命周期值对象。不要把它们混成同一种‘数据类’。"),
    ("类型注解与泛型", "int、str | None、list[Package]、Annotated 和 Literal 既帮助 IDE，也被 FastAPI/Pydantic 读取为运行时校验规则。", "TypedDict 只约束静态形状，不创建运行时模型；Pydantic BaseModel 会真正校验。WorkflowState 与 NameIn 的差异就在这里。"),
    ("HTTP、URL 与 JSON", "HTTP 请求由方法、路径、头、正文组成；JSON 只表达字符串、数字、布尔、数组、对象和 null。", "Bearer Token 放在 Authorization 头；multipart/form-data 传文件；支付宝通知是表单；静态 Logo 由 /static 路径直接读取。"),
    ("FastAPI 路由", "APIRouter 的 prefix 与装饰器路径拼成最终 URL。response_model 在返回前再次校验和裁剪数据。", "同步 def 路由会在线程池执行；async def 在事件循环执行。异步路由里直接做同步 RAG 会阻塞该事件循环。"),
    ("依赖注入 Depends", "Depends 把资源获取从业务函数中抽离。FastAPI 解析依赖图、执行依赖、把返回值注入参数，并在 yield 依赖结束后清理。", "get_session 的 finally 关闭会话；鉴权依赖在路由体之前解码 JWT。依赖失败时，业务函数不会执行。"),
    ("Pydantic v2 校验", "BaseModel 将不可信输入转成可信 Python 对象。Field 描述约束，model_validator(mode='after') 做跨字段规则。", "NameIn 保证人名必须有姓氏；RegisterIn 保证两次密码一致；ConfigDict(from_attributes=True) 允许从 ORM 属性读取响应字段。"),
    ("async/await 与事件循环", "await 暂停当前协程，让循环运行其他任务；它不会自动把同步函数变成非阻塞。", "数据库、SMTP、Redis、RabbitMQ 使用异步 API；retrieve_user_knowledge 与 httpx.Client 是同步调用，应送线程池或改为异步实现。"),
    ("SQLAlchemy ORM", "ORM 把表映射成 Python 类，把查询表达式编译成 SQL。Mapped 与 mapped_column 同时提供类型信息和列定义。", "flush 把内存变更发到数据库但不结束事务；commit 才持久化；expire_on_commit=False 让提交后属性仍可读取。"),
    ("事务、锁与幂等", "事务要求一组状态变化要么全部成功、要么全部回滚。with_for_update 对目标行加悲观锁。", "扣次数和支付入账都锁账户；pay_success 先检查 paid，避免支付宝重复通知重复充值，这就是业务幂等。"),
    ("JWT 身份认证", "JWT 是签名令牌，不是加密保险箱。payload 可被读取，签名只证明内容未被篡改。", "项目区分 access/refresh type，并给出不同有效期；服务端解码后把 user_id 注入路由。fallback_secret 会削弱生产安全。"),
    ("Redis 与 TTL", "Redis 是内存键值数据库。验证码键 register:code:{email} 设置 ex=300，五分钟后自动消失。", "decode_responses=True 让 get 返回 str；连接池复用 TCP 连接。生产中 URL、认证和生命周期应配置化。"),
    ("SMTP 邮件", "SMTP 客户端连接邮件服务器、认证、提交消息；FastMail 封装连接参数与异步发送。", "验证码应先生成、存 Redis、再发送；发送失败后的状态一致性要明确。当前 QQ 邮箱特殊异常被当作成功处理。"),
    ("LangChain 与 Runnable", "ChatDeepSeek 是模型适配器，ChatPromptTemplate 负责模板，| 组合成 Runnable 链，ainvoke 异步调用。", "with_structured_output(NameResultSchema) 要求模型返回符合 Schema 的对象，使下游无需手写脆弱 JSON 解析。"),
    ("提示词与结构化输出", "系统指令、用户约束、历史结果和 RAG 文本共同组成模型上下文。温度越高通常越发散。", "Schema 约束形状，不保证名称质量、域名真实有效或遵循所有软约束；仍需业务校验和失败重试。"),
    ("LangGraph 状态机", "StateGraph 把工作拆成节点和边。supervisor 根据 category 路由到 human/company/pet，节点返回的字典合并回状态。", "END 表示一次运行结束；Checkpoint 用 thread_id 找回上轮状态，让 feedback 只提交增量也能继续。"),
    ("RAG 检索增强生成", "RAG 先从私有资料检索相关片段，再把片段放进提示词，减少模型忽略企业规范的概率。", "它不是训练模型。原文被加载、切块、Embedding、写 Chroma；查询也向量化，再做相似度搜索。"),
    ("Embedding 与向量数据库", "Embedding 把文本映射到高维向量；语义相近文本在向量空间距离更近。", "RecursiveCharacterTextSplitter 使用 300 字块和 50 字重叠；每个用户一个 collection 实现逻辑隔离，但仍需访问控制与删除机制。"),
    ("RabbitMQ 消息队列", "生产者只投递 user_id 和 file_path，Worker 慢慢解析；这样上传接口不用等待向量化完成。", "durable 队列不等于消息持久化；当前 Message 未设置 delivery_mode=PERSISTENT。process() 成功后 ack，异常路径会按库策略处理。"),
    ("支付、签名与 Webhook", "支付链接把用户带到支付宝；真正可信的入账依据是服务端异步通知，而不是浏览器回跳。", "回调必须验签、校验订单、金额和状态，并保证幂等。RSA2 使用商户私钥签名、支付宝公钥验签。"),
]


ADVANCED = [
    Lesson("API 全景矩阵", "项目暴露认证、命名、次数、知识库、Logo、套餐和支付接口；公开接口与鉴权接口必须明确区分。", [("公开", "GET /auth/code、POST /auth/register、POST /auth/login、GET /package/list、支付 return/notify 回调。"), ("需 Access Token", "余额、首次起名、反馈、知识库上传、订单创建和订单查询；源码中的 Logo 生成当前没有鉴权。"), ("运维测试", "GET /mail/test 会发真实邮件，不应在生产无保护暴露。OpenAPI /docs 由 FastAPI 自动生成。")], "api"),
    Lesson("注册与登录时序", "验证码、数据库用户、次数账户和 JWT 组成身份链；任何一步失败都应避免留下半状态。", [("注册", "邮箱校验 → Redis 取码 → UserRepository.create → CreditRepository.create_register_credit → 删除验证码。"), ("登录", "按邮箱查用户 → pwdlib 验证哈希 → 签发 access/refresh。密码明文只在请求和校验瞬间存在。"), ("注意", "用户创建与赠送次数分别开启事务，第二步失败会留下没有次数账户的用户；应合并为同一事务边界。")], "authseq"),
    Lesson("首次起名时序", "业务入口先检查余额，AI 成功后再扣次数，避免模型失败也计费。", [("主链", "JWT → get_balance → generate_names_v2 → LangGraph 专家节点 → 结构化输出 → consume_name_credit → 响应。"), ("并发窗口", "余额检查和扣减分属两个事务；两次并发请求都可能通过预检，后一个在扣减时失败，但 AI 成本已经产生。"), ("修正", "预留/冻结额度，或先原子扣减再在模型失败时补偿；同时给请求设置幂等键。")], "nameseq"),
    Lesson("多轮反馈与会话记忆", "thread_id 是恢复状态的钥匙。Checkpoint 合并上轮需求、history_names 和新 feedback，再重新走同类专家节点。", [("状态", "build_node_result 把模型结果同时存入 final_output 和可读 history_names，并清空已消费的 feedback。"), ("越权风险", "feedback_names 接收 user_id 却没有把它写入查询条件或比对恢复状态；拿到他人 thread_id 可能访问或改写其上下文。"), ("计费风险", "反馈接口没有 Session，也不检查/扣减次数；需要明确产品策略并实施限流。")], "feedback"),
    Lesson("企业名 + RAG + 域名链", "企业节点是项目最复杂的 AI 路径：同步检索私有资料、调用模型、并发查询五个域名。", [("输入增强", "query 由 other + 固定行业词组成，检索 top_k=2，结果原样放入 prompt。"), ("域名", "asyncio.gather 并行 TCP WHOIS，减少五次串行等待；只检查 .com，返回文本状态。"), ("边界", "模型生成的 domain 可能格式错误；WHOIS 文本协议也可能限流。应做格式校验、缓存和正式注册商 API 兜底。")], "company"),
    Lesson("知识库上传与 Worker 时序", "HTTP 进程只保存文件并投递消息，Worker 读取文件、切块、向量化、写入按用户隔离的 Chroma collection。", [("解耦价值", "大文件处理不占用请求等待时间；prefetch_count=1 防止单 Worker 同时加载多个大文档。"), ("失败语义", "接口返回成功只表示已入队，不表示知识库已完成；缺少任务 ID、状态表、重试队列与死信队列。"), ("安全", "file.filename 直接参与路径拼接，需 Path.name 净化、扩展名/MIME/大小校验、随机服务端文件名和恶意文件扫描。")], "ragseq"),
    Lesson("支付创建与回调时序", "订单先本地落 pending，再生成支付宝链接；Webhook 验签后锁订单与账户，一次事务完成 paid + 充值 + 流水。", [("可信链", "notify_data 去掉 sign/sign_type → 支付宝公钥验签 → 检查 trade_status、订单存在和金额一致。"), ("幂等", "锁订单后若 status 已 paid 直接返回 False；重复回调不会重复增加次数。"), ("改进", "校验 seller_id/app_id，记录原始通知，统一时区；浏览器 return_url 只展示结果，不应承担入账。")], "payseq"),
    Lesson("数据库 ER 模型", "五类业务实体形成两个主链：用户-次数-流水，以及用户-订单-套餐。", [("约束", "user.email、user_credit.user_id、user_order.order_no 唯一；外键保护引用完整性。"), ("快照字段", "订单复制 amount 与 credit_count，避免套餐后来改价影响历史订单，这是正确的账务快照设计。"), ("缺少", "没有 ORM relationship、订单过期时间、退款字段、软删除和审计操作者；生产账务还需更完整状态机。")], "erd"),
    Lesson("环境变量与启动契约", "源码读取 24 个环境变量，但仓库没有 .env.example 和锁定依赖文件；新维护者难以稳定复现。", [("启动必需", "DB_URI、LANGGRAPH_DB_URI、DEEPSEEK_API_KEY 在导入/启动阶段关键；RABBITMQ_URL 对上传和 Worker 必需。"), ("功能配置", "JWT、邮件、支付宝、DashScope/万相、APP_BASE_URL；Redis URL 当前硬编码。"), ("建议", "引入 pydantic-settings 单一 Settings，启动时分组校验；提交 .env.example，使用 pyproject.toml + lock。")], "env"),
    Lesson("错误处理与可观测性", "当前大量 print、宽泛 except 和字符串错误返回，适合原型调试但难以运营。", [("日志", "使用结构化日志携带 request_id、user_id、thread_id、order_no；严禁打印 Token 片段和敏感参数。"), ("异常", "定义领域异常并在 FastAPI 统一映射；第三方失败要记录状态码、耗时、可重试性，而不是全部归为 500。"), ("指标", "请求延迟、模型成功率、结构化输出失败率、队列积压、RAG 块数、支付回调失败、余额异常。")], "observe"),
    Lesson("测试策略", "现有 .http 文件是有价值的人工冒烟脚本，但缺少可自动回归的测试套件。", [("单元", "测试 Schema 校验、JWT type、订单号、prompt 拼装、域名格式、build_node_result；外部服务全部 mock。"), ("集成", "临时 PostgreSQL/Redis/RabbitMQ/Chroma 验证事务、Checkpoint、消息 ack 和用户隔离。"), ("端到端", "注册 → 登录 → 起名 → 反馈 → 充值；支付用沙箱签名样本，检查重复通知只入账一次。")], "test"),
    Lesson("安全审计：高优先级", "审计按影响与可利用性排序。这里是源码事实导出的维护清单，不代表已经发生攻击。", [("P0/P1", "feedback thread_id 未校验归属；上传文件名路径穿越；JWT 存在 fallback_secret；/mail/test 与 /logos/generate 无鉴权/限流。"), ("输入输出", "支付成功 HTML 直接插入异常文本和订单字段；上传未限制类型大小；RAG 文本可形成提示词注入。"), ("秘密", "所有密钥应来自安全配置；日志不可泄露 Token；支付宝 debug=True 不能直接用于生产。")], "security"),
    Lesson("并发、一致性与成本", "AI 调用比数据库操作昂贵且慢，额度与请求并发必须围绕成本设计。", [("已做对", "扣减与入账对账户行加锁；支付重复通知幂等；域名查询使用 gather。"), ("竞态", "余额预检与扣减分离；注册用户与赠送额度分事务；订单号只有秒级时间 + 六位随机数。"), ("方案", "额度预占表、唯一请求键、重试策略、数据库唯一约束兜底；对 LLM 和图片任务加入超时、并发阈值与熔断。")], "concurrency"),
    Lesson("性能分析", "当前瓶颈更可能是外部模型、同步向量检索和文件处理，而不是 Python 语法本身。", [("阻塞点", "async 企业节点直接调用同步 Chroma/Ollama；Logo 同步 httpx 最长 180 秒；Worker 中同步函数占住消费协程。"), ("数据库", "每个仓储方法单独开事务，增加往返；echo=True 会产生大量日志；连接池参数需按进程数和数据库上限计算。"), ("优化顺序", "先测量 p95；再隔离长任务、使用 AsyncClient/to_thread；然后缓存 RAG/WHOIS，最后才考虑微观代码优化。")], "performance"),
    Lesson("可维护性审计", "项目能力完整，但文件呈现迭代痕迹：重复导入、旧实现并存、注释残留和配置分散。", [("重复", "auth_router、name_router、pay_router 多次中途 import；models/__init__.py 重复导入 user；nametools.py 已被 workflow.py 取代但仍保留。"), ("边界", "路由承担较多支付 HTML 与状态编排；建议增加 service/use-case 层和 payment gateway 接口。"), ("规范", "统一 Ruff/Black/Mypy、docstring、异常类型和命名；把路由响应、领域对象、ORM 对象边界写成约定。")], "maintain"),
    Lesson("部署拓扑与运行手册", "生产部署至少包含 API 进程、RAG Worker、业务数据库、Checkpoint PostgreSQL、Redis、RabbitMQ、Chroma 卷和 Ollama。", [("启动顺序", "数据库/Redis/RabbitMQ/Ollama → Alembic upgrade → Checkpoint setup → Worker → Uvicorn/Gunicorn。"), ("持久卷", "业务库、Checkpoint、chroma_rag_db、uploads/static 需要备份策略；静态 Logo 更适合对象存储。"), ("健康检查", "分别验证数据库、Redis、RabbitMQ、模型与外部 API；lifespan 失败应让实例不接流量。")], "deploy"),
    Lesson("如何新增一种命名类别", "以‘产品名’为例，改动要贯穿输入契约、路由状态、工作流节点、测试和计费。", [("代码", "扩展 CategoryLiteral/FeedbackIn Literal；新增 product_naming_node；加入 StateGraph 节点、category_map、条件边和 END。"), ("提示词", "定义领域原则与结构化字段，决定是否使用 RAG、域名或 Logo；不要在路由里复制模型调用。"), ("验证", "测试首次生成、反馈恢复、非法类别、额度扣减和旧 thread 的兼容；必要时给 checkpoint 状态加版本。")], "extend"),
    Lesson("如何修改核心提示词", "提示词是产品逻辑，应像代码一样版本化、测试和观察，而不是只凭感觉改字符串。", [("改前", "收集失败样本，明确要提高的是格式遵循、文化质量、避讳、品牌传播还是域名可用率。"), ("改动", "把共同规则与类别规则拆开；给 RAG 内容清晰边界；明确冲突优先级；保持 Schema 与文字要求一致。"), ("上线", "记录 prompt_version，离线回放样本并做 A/B；监控 token、延迟、失败率和人工评分。")], "prompt"),
    Lesson("第一小时接手路线", "先让系统边界和风险进入脑中，再运行代码；不要从 530 行 workflow.py 第一行硬啃。", [("0-20 分钟", "读 main.py、README 的启动段、目录页和环境变量矩阵；画出外部依赖。"), ("20-40 分钟", "沿 /name/generate：name_router → credit_repo → workflow → schema；再看数据库模型。"), ("40-60 分钟", "检查 git status、配置缺口和高优先级安全项；用 test_name.http 了解预期请求，但不要用真实支付/邮件密钥。")], "hour"),
    Lesson("第一周学习计划", "目标是从‘能启动’进阶到‘能安全修改并解释权衡’。", [("第 1-2 天", "搭环境、迁移数据库、跑手工链；补自动测试基线。"), ("第 3-4 天", "理解 LangGraph checkpoint、RAG collection 隔离和支付幂等；用断点观察真实状态。"), ("第 5-7 天", "修复高优先级风险、引入统一 Settings/日志、绘制运行仪表板并完成一次小功能演练。")], "week"),
    Lesson("演进路线图", "从原型到可运营产品应分阶段降低风险，而不是一次性重写。", [("阶段 A", "锁依赖与配置；补测试；修复鉴权、上传、fallback secret、阻塞调用和回跳入账边界。"), ("阶段 B", "任务状态、重试/死信、对象存储、结构化日志与指标；拆出 use-case/service。"), ("阶段 C", "Prompt 版本、评测集、配额预占、租户级数据治理、模型降级与成本控制。")], "roadmap"),
    Lesson("最终掌握检查表", "如果下面的问题都能脱离文档回答，你已经具备独立维护 AINAME 的基础。", [("解释", "为什么 models/__init__ 要导入模型？为何 Checkpoint 用 thread_id？为什么支付回调必须锁订单？为什么 Schema 不能保证语义正确？"), ("追踪", "能从任一 API 追到依赖、仓储、事务、外部服务和响应；能指出每个 await 前后控制权与失败窗口。"), ("修改", "能新增类别、替换模型、调整计费、扩展迁移，并用自动测试与指标证明没有破坏旧链。")], "check"),
    Lesson("结语：从源码读者到维护者", "AINAME 已经把 AI Demo 推进到有身份、记忆、知识、计费与支付的产品原型。真正的下一步是把边界变得可验证。", [("核心认识", "项目的价值在编排：模型只是一个节点；可靠性来自输入契约、状态、事务、隔离、幂等和可观测性。"), ("维护原则", "任何新功能都回答四问：数据归谁、失败怎么恢复、并发会怎样、成本由谁承担。"), ("交接完成", "本教材覆盖当前 50 个文件、关键行与调用链。源码变化后应重新生成文件清单、行号截图和审计结论。")], "final"),
]

# Keep the book at exactly 100 pages. Performance is covered by the concurrency
# and deployment lessons; the mastery checklist is folded into the conclusion.
ADVANCED = [lesson for lesson in ADVANCED if lesson.title not in {"性能分析", "最终掌握检查表"}]


def file_role(rel: str) -> tuple[str, str, str]:
    name = rel.replace("\\", "/")
    exact = {
        "main.py": ("应用入口", "创建 FastAPI、管理 LangGraph 生命周期、挂载静态目录并注册全部路由。", "导入 workflow 会立即校验模型密钥和记忆库 URI；缺失配置会使应用在监听端口前失败。"),
        "dependencies.py": ("资源依赖", "向路由提供 FastMail 和 AsyncSession，并用 yield/finally 保证会话关闭。", "会话关闭不等于事务提交；提交/回滚由仓储中的 session.begin 管理。"),
        "core/workflow.py": ("命名中枢", "定义状态、三类专家、条件路由、PostgreSQL Checkpoint 和首次/反馈用例。", "这是最高耦合文件：模型、RAG、WHOIS、状态机和生命周期都在此汇合。"),
        "routers/pay_router.py": ("支付协议层", "创建订单、展示回跳、查询订单并接收支付宝异步通知。", "Webhook 路径不能加用户 JWT，但必须严格验签、验金额、验状态并保持幂等。"),
        "routers/rag_router.py": ("知识库入口", "保存上传文件并把解析任务投递到 RabbitMQ。", "文件名、大小和类型均属不可信输入；当前实现需要路径净化和任务状态。"),
        "rag_worker.py": ("异步消费者", "以 prefetch=1 消费向量化任务，调用 RAG 服务写入 Chroma。", "process_and_store_file 是同步函数，Worker 并发扩容需要结合 CPU/内存和 Ollama 吞吐。"),
        "core/logo_tools.py": ("图像生成适配器", "构造万相请求、解析图片 URL、下载并保存为静态 PNG。", "同步网络 I/O 最长 180 秒；应转成异步客户端或后台任务，并限制匿名调用。"),
        "models/__init__.py": ("数据库基础设施", "创建异步 Engine、SessionFactory 和带命名约定的 Declarative Base。", "DB_URI 为空会在导入时失败；echo=True 不适合高流量生产。尾部导入让迁移发现所有模型。"),
        "schemas/name_schemas.py": ("AI/HTTP 双重契约", "约束命名输入、模型结构化输出、首次结果和反馈请求。", "NameSchema 对所有类别都要求 domain，因此人名/宠物名也依赖模型填写域名，契约与业务语义不完全一致。"),
        "repository/order_repo.py": ("账务仓储", "创建订单并在行锁事务内完成支付幂等、次数增加和流水写入。", "这是事务设计最成熟的文件；仍需订单号冲突兜底、时区与退款状态。"),
        "README.md": ("运行说明", "记录项目定位、技术栈、环境变量、启动顺序、接口示例与故障排查。", "文档提到依赖安装，但仓库没有 requirements.txt/pyproject.toml；MySQL 与通用 DB_URI 表述也需统一。"),
    }
    if name in exact:
        return exact[name]
    if name.startswith("routers/"):
        return "HTTP 路由", "把 URL、鉴权依赖、Schema 与核心/仓储用例连接起来。", "路由应保持薄层，避免承载长事务、阻塞 I/O 或可复用领域规则。"
    if name.startswith("repository/"):
        return "数据仓储", "封装 SQLAlchemy 查询与事务，让路由不直接依赖 SQL 细节。", "检查每个方法的事务边界、锁、返回对象生命周期和并发语义。"
    if name.startswith("models/"):
        return "ORM 模型", "定义业务表字段、类型、默认值、唯一约束、索引和外键。", "Python default 只在 ORM 创建时生效；数据库约束才是跨进程一致性的最终防线。"
    if name.startswith("schemas/"):
        return "数据契约", "用 Pydantic 校验输入、描述 OpenAPI 并序列化响应。", "Schema 变化等于 API 变化；新增必填字段需考虑旧客户端和历史 Checkpoint。"
    if name.startswith("alembicdb/versions/"):
        return "数据库迁移", "用 upgrade/downgrade 描述表结构从一个版本到下一个版本的变化。", "迁移链必须线性可追踪；生产执行前要备份并验证 downgrade 是否真能恢复。"
    if name.startswith("alembicdb/") or name == "alembic.ini":
        return "迁移配置", "把 SQLAlchemy metadata、数据库 URL 与 Alembic 运行环境连接。", "env.py 的中文注释曾出现编码痕迹；配置从 DB_URI 注入，迁移与应用需使用同一数据库。"
    if name.startswith("core/"):
        return "核心能力", "封装鉴权、邮件、支付、模型、RAG、Redis、域名或 Logo 等可复用能力。", "外部调用需要超时、重试、日志、限流和可替换接口；模块级单例会影响测试隔离。"
    if name.endswith(".http"):
        return "手工接口测试", "按顺序保存可执行 HTTP 请求和响应变量，支持本地冒烟验证。", "它不是自动断言测试；样例邮箱、订单号和验证码不可视为稳定测试数据。"
    if name.endswith(".bat"):
        return "Windows 启动脚本", "检测/启动本机 Redis，然后用 uvicorn --reload 启动开发服务器。", "路径写死到 Program Files\\Redis，只适合特定开发机；reload 不是生产配置。"
    if name.endswith(".txt"):
        return "RAG 示例语料", "演示上传企业命名规则并被切块、向量化、检索。", "语料属于用户输入，可能包含提示词注入；读取、展示和日志记录都要按不可信文本处理。"
    return "项目辅助文件", "支持项目配置、模板或说明。", "维护时检查它是否仍与当前代码和启动方式一致。"


def inspect_file(path: Path) -> dict:
    text = read_source(path)
    result = {"lines": len(text.splitlines()), "imports": [], "symbols": [], "env": []}
    if path.suffix == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return result
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                result["imports"].extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                result["imports"].append(node.module)
            elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                result["symbols"].append((node.name, node.lineno, type(node).__name__))
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and node.func.attr == "getenv" and node.args and isinstance(node.args[0], ast.Constant)):
                result["env"].append(str(node.args[0].value))
    return result


def make_code_shot(path: Path, index: int) -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    out = TMP_DIR / f"code_{index:02d}.png"
    lines = read_source(path).splitlines()
    if len(lines) > 18:
        # Prefer the first meaningful definition/decorator area over a wall of comments.
        start = next((max(0, i - 2) for i, line in enumerate(lines)
                      if re.match(r"\s*(async\s+def|def|class|@router\.)", line)), 0)
        lines = lines[start:start + 18]
        first_no = start + 1
    else:
        first_no = 1
    img = Image.new("RGB", (1500, 650), "#0B172A")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(str(FONT_CODE), 27)
    font_cn = ImageFont.truetype(str(FONT_CN), 27)
    small = ImageFont.truetype(str(FONT_CODE_BOLD), 24)
    draw.rounded_rectangle((0, 0, 1499, 649), radius=22, fill="#0B172A", outline="#2D4868", width=3)
    draw.text((36, 24), path.relative_to(ROOT).as_posix(), font=small, fill="#8DD7FF")
    draw.ellipse((1380, 28, 1400, 48), fill="#FF6B6B")
    draw.ellipse((1415, 28, 1435, 48), fill="#FFD166")
    draw.ellipse((1450, 28, 1470, 48), fill="#5AD18A")
    y = 78
    if not lines:
        draw.text((90, y + 120), "（空包标记文件：通过存在性声明 Python 包边界）", font=font_cn, fill="#C8D8EA")
    for offset, line in enumerate(lines):
        no = first_no + offset
        clean = line.expandtabs(4)
        if len(clean) > 92:
            clean = clean[:91] + "…"
        draw.text((32, y), f"{no:>4}", font=font, fill="#607D9D")
        code_font = font_cn if any(ord(ch) > 127 for ch in clean) else font
        color = "#E6EDF3"
        stripped = clean.lstrip()
        if stripped.startswith("#") or stripped.startswith("rem "):
            color = "#7FB38A"
        elif re.match(r"(from|import|class|def|async|return|if|else|try|except|with|await)\b", stripped):
            color = "#B9A7FF"
        draw.text((125, y), clean, font=code_font, fill=color)
        y += 30
    img.save(out, optimize=True)
    return out


def draw_code_page(c: canvas.Canvas, page_no: int, path: Path, shot: Path) -> None:
    rel = path.relative_to(ROOT).as_posix()
    info = inspect_file(path)
    role, purpose, warning = file_role(rel)
    y = draw_header(c, page_no, "第四篇 · 逐文件源码精读", rel, f"{role}｜{info['lines']} 行｜以下截图直接来自当前工作区。")
    c.setFont("CNB", 10.5)
    c.setFillColor(NAVY)
    c.drawString(mm(16), y, "为什么存在")
    y = draw_wrapped(c, purpose, mm(16), y - mm(6), PAGE_W - mm(32), size=8.7, leading=12, max_lines=4)
    symbols = info["symbols"]
    imports = sorted(set(info["imports"]))
    sym_text = "；".join(f"{n}()@L{ln}" if k != "ClassDef" else f"class {n}@L{ln}" for n, ln, k in symbols[:10]) or "无显式函数/类；该文件主要通过配置、常量、请求样例或包标记发挥作用。"
    dep_text = "、".join(imports[:9]) or "无 Python 导入；依赖由其文件格式或调用者解释。"
    if len(imports) > 9:
        dep_text += f" 等 {len(imports)} 项"
    top = y - mm(2)
    draw_card(c, mm(16), top, mm(87), "符号与调用入口", sym_text, BLUE, mm(31))
    draw_card(c, mm(107), top, mm(87), "依赖与加载影响", dep_text, CYAN, mm(31))
    img_y = mm(48)
    c.drawImage(str(shot), mm(16), img_y, width=mm(178), height=mm(77), preserveAspectRatio=False, mask="auto")
    c.setFont("CN", 7.2)
    c.setFillColor(MUTED)
    c.drawString(mm(16), mm(44), "逐行读法：先看导入/定义的加载期副作用，再沿参数、分支、await、事务、外部 I/O 与返回值追踪。")
    c.setFillColor(HexColor("#FFF4E5"))
    c.roundRect(mm(16), mm(20), mm(178), mm(19), mm(2), fill=1, stroke=0)
    c.setFont("CNB", 8.5)
    c.setFillColor(AMBER)
    c.drawString(mm(21), mm(33), "删除或修改会影响什么")
    draw_wrapped(c, warning, mm(21), mm(27.5), mm(168), size=7.7, leading=9.5, color=INK, max_lines=2)
    draw_footer(c, page_no)


def draw_diagram(c: canvas.Canvas, kind: str, x: float, y: float, w: float, h: float) -> None:
    c.setFillColor(CARD)
    c.setStrokeColor(LINE)
    c.roundRect(x, y, w, h, mm(3), fill=1, stroke=1)
    def node(cx: float, cy: float, label: str, color: Color = BLUE, width: float = mm(31)):
        c.setFillColor(color)
        c.roundRect(cx - width / 2, cy - mm(6), width, mm(12), mm(2), fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("CN", 7.5)
        c.drawCentredString(cx, cy - mm(1.2), label)
    def arrow(x1: float, y1: float, x2: float, y2: float):
        c.setStrokeColor(MUTED)
        c.setLineWidth(1.2)
        c.line(x1, y1, x2, y2)
        import math
        a = math.atan2(y2-y1, x2-x1)
        for delta in (2.55, -2.55):
            c.line(x2, y2, x2 + mm(3)*math.cos(a+delta), y2 + mm(3)*math.sin(a+delta))
    if kind == "mindmap":
        node(x+w/2, y+h/2, "AINAME", NAVY, mm(34))
        points = [(0.18,0.72,"身份/计费"),(0.5,0.82,"AI 工作流"),(0.82,0.72,"RAG/知识"),(0.18,0.28,"支付/订单"),(0.5,0.18,"数据/记忆"),(0.82,0.28,"Logo/域名")]
        for px,py,label in points:
            cx,cy=x+w*px,y+h*py; arrow(x+w/2,y+h/2,cx,cy); node(cx,cy,label,CYAN)
    elif kind in {"request","nameseq","authseq","ragseq","payseq"}:
        labels = {
            "request":["客户端","Uvicorn","FastAPI/DI","路由用例","数据库/外部服务","JSON 响应"],
            "nameseq":["Bearer JWT","余额预检","LangGraph","专家节点","结构化结果","扣减次数"],
            "authseq":["邮箱验证码","Redis TTL","创建用户","赠送次数","密码校验","JWT"],
            "ragseq":["上传文件","本地保存","RabbitMQ","Worker","切块/Embedding","Chroma"],
            "payseq":["创建 pending","支付宝收银台","Webhook","验签/验金额","行锁幂等","充值+流水"],
        }[kind]
        gap=w/(len(labels)+1); cy=y+h/2
        for i,label in enumerate(labels):
            cx=x+gap*(i+1); node(cx,cy,label,BLUE if i%2==0 else CYAN,mm(27))
            if i: arrow(x+gap*i+mm(14),cy,x+gap*(i+1)-mm(14),cy)
    elif kind == "layers":
        labels=[("HTTP / Router",BLUE),("Core / Use case",CYAN),("Repository",GREEN),("ORM + 外部基础设施",NAVY)]
        for i,(label,color) in enumerate(labels):
            yy=y+h-mm(18)-i*mm(17); node(x+w/2,yy,label,color,mm(85))
            if i: arrow(x+w/2,yy+mm(11),x+w/2,yy+mm(7))
    elif kind == "erd":
        coords={"user":(.16,.58),"user_credit":(.40,.75),"credit_log":(.68,.75),"user_order":(.42,.35),"package":(.75,.35)}
        for label,(px,py) in coords.items(): node(x+w*px,y+h*py,label,NAVY if label=="user" else BLUE,mm(34))
        for a,b in [("user","user_credit"),("user","credit_log"),("user","user_order"),("package","user_order")]:
            ax,ay=coords[a]; bx,by=coords[b]; arrow(x+w*ax,y+h*ay,x+w*bx,y+h*by)
    elif kind == "context":
        node(x+w/2,y+h/2,"FastAPI AINAME",NAVY,mm(45))
        pts=[(.14,.7,"DeepSeek"),(.38,.82,"PostgreSQL"),(.65,.82,"Redis/RabbitMQ"),(.86,.7,"支付宝"),(.14,.28,"Ollama/Chroma"),(.38,.16,"SMTP"),(.65,.16,"DashScope"),(.86,.28,"WHOIS")]
        for px,py,label in pts:
            cx,cy=x+w*px,y+h*py; arrow(x+w/2,y+h/2,cx,cy); node(cx,cy,label,CYAN,mm(31))
    else:
        node(x+w*.18,y+h/2,"输入",BLUE); node(x+w*.5,y+h/2,"AINAME 核心",NAVY,mm(45)); node(x+w*.82,y+h/2,"输出",GREEN)
        arrow(x+w*.34,y+h/2,x+w*.40,y+h/2); arrow(x+w*.60,y+h/2,x+w*.66,y+h/2)


def draw_lesson(c: canvas.Canvas, page_no: int, lesson: Lesson, chapter: str) -> None:
    y = draw_header(c, page_no, chapter, lesson.title, lesson.lead)
    if lesson.diagram:
        draw_diagram(c, lesson.diagram, mm(16), mm(92), mm(178), mm(67))
        y = mm(84)
        cols = len(lesson.sections)
        w = (mm(178) - mm(4)*(cols-1))/cols
        for i,(title,body) in enumerate(lesson.sections):
            draw_card(c, mm(16)+i*(w+mm(4)), y, w, title, body, [BLUE,CYAN,GREEN][i%3], mm(55))
    else:
        for i,(title,body) in enumerate(lesson.sections):
            y = draw_card(c, mm(16), y, mm(178), title, body, [BLUE,CYAN,GREEN,AMBER][i%4], mm(40))
    draw_footer(c, page_no)


def draw_cover(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY); c.rect(0,0,PAGE_W,PAGE_H,fill=1,stroke=0)
    c.setFillColor(BLUE); c.circle(PAGE_W-mm(15),PAGE_H-mm(28),mm(48),fill=1,stroke=0)
    c.setFillColor(CYAN); c.circle(mm(8),mm(16),mm(34),fill=1,stroke=0)
    c.setFillColor(HexColor("#163A5F")); c.roundRect(mm(18),mm(42),mm(174),mm(205),mm(5),fill=1,stroke=0)
    c.setFont("CN",10); c.setFillColor(HexColor("#8DD7FF")); c.drawString(mm(28),mm(227),"项目创始人交接手册 × 大学教材 × 源码审计报告")
    c.setFont("CNB",31); c.setFillColor(white); c.drawString(mm(28),mm(197),"AINAME")
    c.setFont("CNB",25); c.drawString(mm(28),mm(179),"项目源码完全解析教材")
    c.setFont("CN",11); c.setFillColor(HexColor("#C8D8EA"))
    draw_wrapped(c,"从 HTTP 请求、异步执行与数据库事务，到 LangChain、LangGraph、RAG、向量检索、域名、Logo 与支付宝支付。",mm(28),mm(160),mm(150),size=11,leading=18,color=HexColor("#C8D8EA"))
    labels=[("50","源码/配置文件"),("100","教学页面"),("24","环境变量"),("7","业务路由模块")]
    for i,(num,label) in enumerate(labels):
        x=mm(28)+(i%2)*mm(78); y=mm(114)-(i//2)*mm(30)
        c.setFillColor(HexColor("#0E2742")); c.roundRect(x,y,mm(70),mm(22),mm(3),fill=1,stroke=0)
        c.setFont("CodeB",16); c.setFillColor(HexColor("#62D6FF")); c.drawString(x+mm(6),y+mm(8),num)
        c.setFont("CN",8); c.setFillColor(white); c.drawString(x+mm(24),y+mm(9),label)
    c.setFont("CN",8); c.setFillColor(HexColor("#A9C0D6")); c.drawString(mm(28),mm(55),"基于工作区源码快照 · 2026-08-05 · Asia/Hong_Kong")
    c.setFont("CN",7.5); c.drawRightString(PAGE_W-mm(20),mm(12),"001 / 100")


def build() -> None:
    register_fonts()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    files = source_files()
    if len(files) != 50:
        raise RuntimeError(f"Expected 50 source/config files, found {len(files)}: {[str(p) for p in files]}")
    shots = [make_code_shot(path, i) for i, path in enumerate(files, 1)]
    c = canvas.Canvas(str(PDF_PATH), pagesize=A4, pageCompression=1)
    c.setTitle("AINAME 项目源码完全解析教材")
    c.setAuthor("Codex")
    c.setSubject("AINAME source code textbook and engineering audit")
    page_no = 1
    draw_cover(c); c.showPage(); page_no += 1
    for lesson in INTRO:
        draw_lesson(c,page_no,lesson,"第一篇 · 项目整体认知"); c.showPage(); page_no += 1
    for title,base,project in CONCEPTS:
        lesson=Lesson(title,base,[("工作原理",base),("在 AINAME 中",project),("删除或误改的后果","概念不是装饰：相关代码承担真实边界。删除校验会让不可信数据进入核心；删除 await/事务/锁会改变执行顺序与一致性；替换库时必须保持同一契约。")])
        draw_lesson(c,page_no,lesson,"第二篇 · 技术栈基础课"); c.showPage(); page_no += 1
    for path,shot in zip(files,shots):
        draw_code_page(c,page_no,path,shot); c.showPage(); page_no += 1
    for lesson in ADVANCED:
        draw_lesson(c,page_no,lesson,"第五篇 · 调用链、审计与交接");
        if page_no < 100: c.showPage()
        page_no += 1
    if page_no != 101:
        raise RuntimeError(f"Expected 100 pages, generated {page_no-1}")
    c.save()
    reader=PdfReader(str(PDF_PATH))
    if len(reader.pages)!=100:
        raise RuntimeError(f"Final PDF has {len(reader.pages)} pages")
    print(PDF_PATH)
    print(f"pages={len(reader.pages)} bytes={PDF_PATH.stat().st_size}")


if __name__ == "__main__":
    build()

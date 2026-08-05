import os
import uuid
from typing import Any, Dict, List, Literal, TypedDict

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from pydantic import SecretStr

from core.rag_service import retrieve_user_knowledge
from schemas.name_schemas import (
    FeedbackIn,
    NameIn,
    NameResultSchema,
)


load_dotenv()


# ==================== 工作流状态 ====================

class WorkflowState(TypedDict):
    user_id: int
    category: str
    surname: str
    gender: str
    length: str
    other: str | None
    exclude: List[str]

    # 多轮记忆字段
    feedback: str
    history_names: str

    # 最终返回结果
    final_output: Dict[str, Any]


# ==================== 初始化大模型 ====================

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

if not deepseek_api_key:
    raise RuntimeError(
        "没有读取到 DEEPSEEK_API_KEY，请检查 .env 文件"
    )


llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=SecretStr(deepseek_api_key),
    temperature=1,
)


# 强制大模型按照 NameResultSchema 输出
structured_llm = llm.with_structured_output(
    NameResultSchema
)


# ==================== 公共辅助函数 ====================

def build_feedback_instruction(
    state: WorkflowState,
) -> str:
    """
    判断当前请求是不是微调请求。

    第一次生成时：
    feedback 和 history_names 都为空，返回空字符串。

    第二次及以后：
    同时存在 feedback 和 history_names，
    就把上一轮结果和用户修改意见加入提示词。
    """

    feedback = state.get("feedback", "")
    history_names = state.get("history_names", "")

    if not feedback or not history_names:
        return ""

    return f"""
🟣 警告：这是一次微调请求！

【上一轮生成的名字】
{history_names}

【用户最新修改意见】
{feedback}

请严格保留上一轮中用户满意的部分，
仅根据用户的最新修改意见，对上一轮名字进行迭代优化。

绝不能无视历史名字重新随机生成。
"""


def build_node_result(
    response: Any,
) -> Dict[str, Any]:
    """
    把大模型结果整理成工作流状态。

    final_output：
    返回给前端的结构化结果。

    history_names：
    保存到 PostgreSQL，供下一轮微调使用。

    feedback：
    本轮意见已经使用完毕，所以清空。
    """

    if response is None or not hasattr(response, "names"):
        raise ValueError(
            "模型没有返回符合 NameResultSchema 的结构化结果"
        )

    memory_list = [
        f"【{name_item.name}】寓意：{name_item.moral}"
        for name_item in response.names
    ]

    names_str = "\n".join(memory_list)

    return {
        "final_output": response.model_dump(),
        "history_names": names_str,
        "feedback": "",
    }


# ==================== 节点函数 ====================

async def supervisor_node(
    state: WorkflowState,
) -> Dict[str, Any]:
    """
    主管节点。

    当前主要负责进入条件路由，
    后续可以增加日志、参数清洗或意图识别。
    """

    return {}


async def human_naming_node(
    state: WorkflowState,
) -> Dict[str, Any]:
    """人名专家节点。"""

    feedback_instruction = build_feedback_instruction(
        state
    )

    prompt = f"""
你是一位精通汉语言文学与传统文化的命名专家。
请为用户创作富有文化底蕴的人名。

【用户初始需求】

姓氏：{state["surname"]}
性别倾向：{state["gender"]}
字数限制：{state["length"]}
其他具体要求：{state["other"] or "无"}
避讳排除字：{"、".join(state["exclude"]) or "无"}

{feedback_instruction}

【起名原则】

1. 平仄协调，名字自然顺口。
2. 优先从《诗经》《楚辞》或唐诗宋词中汲取灵感。
3. 必须满足用户提出的字数、性别和避讳要求。
4. 如果这是微调请求，必须严格执行用户的最新修改意见。
5. 给出 5 个候选方案。
"""

    response = await structured_llm.ainvoke(prompt)

    return build_node_result(response)

from core.domain_tools import check_com_domain
import asyncio
async def company_naming_node(
    state: WorkflowState,
) -> Dict[str, Any]:
    """企业品牌节点，融合 RAG 增强检索。"""

    current_user_id = state["user_id"]

    # 根据用户需求检索该用户自己的知识库
    search_query = (
        f"{state['other']} 品牌命名规范 行业词汇"
    )

    rag_context = retrieve_user_knowledge(
        query=search_query,
        user_id=current_user_id,
    )

    feedback_instruction = build_feedback_instruction(
        state
    )

    prompt = f"""
你是一位精通商业品牌传播的资深顾问。
请根据用户需求，创作符合商业规范的公司名称。

【用户初始需求】

行业或核心诉求：{state["other"] or "无"}
字数限制：{state["length"]}
避讳排除字：{"、".join(state["exclude"]) or "无"}

【用户的专属私有知识库参考】

{rag_context}

{feedback_instruction}
 核心纪律（最高优先级）：
    1. 必须遵守知识库和修改意见。
    2. 你必须为每个公司名构思一个绝佳的 .com 英文或拼音域名，填入 domain 字段（例如：
hema.com 或 greenearth.com)

【起名原则】

1. 优先参考用户专属知识库中的规则和行业词汇。
2. 名字应当适合商业传播，容易识别和记忆。
3. 必须满足用户提出的字数和避讳要求。
4. 如果这是微调请求，必须严格执行用户的最新修改意见。
5. 给出 5 个候选方案。

"""

    response = await structured_llm.ainvoke(prompt)
    if response is None or not hasattr(response, "names"):
        raise ValueError(
        "模型没有返回符合 NameResultSchema 的结构化结果"
        )

# 为每个域名创建查询任务
    tasks = [
        check_com_domain(name_item.domain)
        for name_item in response.names
    ]

# 5 个域名并发查询
    statuses = await asyncio.gather(*tasks)

# 把查询结果写回每个 NameSchema 对象
    for name_item, status in zip(response.names, statuses):
        name_item.domain_status = status

    # 查询并写回之后，再返回
    return build_node_result(response)



async def pet_naming_node(
    state: WorkflowState,
) -> Dict[str, Any]:
    """宠物起名节点。"""

    feedback_instruction = build_feedback_instruction(
        state
    )

    prompt = f"""
你是一位充满创意的宠物达人。
请为用户的宠物创作富有灵性的名字。

【用户初始需求】

宠物特征或性格：{state["other"] or "无"}
字数限制：{state["length"]}
避讳排除字：{"、".join(state["exclude"]) or "无"}

{feedback_instruction}

【起名原则】

1. 名字亲切好记。
2. 名字应当富有画面感、灵性或软萌感。
3. 必须满足用户提出的字数和避讳要求。
4. 如果这是微调请求，必须严格执行用户的最新修改意见。
5. 给出 5 个候选方案。

每个方案必须包含：

- name：宠物名字
- reference：名字的创作来源或命名思路
- moral：名字的含义和寓意
"""

    response = await structured_llm.ainvoke(prompt)

    return build_node_result(response)


# ==================== 路由逻辑 ====================

def route_by_category(
    state: WorkflowState,
) -> Literal["human", "company", "pet"]:
    """根据 category 选择对应的起名专家。"""

    category_map: Dict[
        str,
        Literal["human", "company", "pet"],
    ] = {
        "人名": "human",
        "企业名": "company",
        "宠物名": "pet",
    }

    return category_map.get(
        state.get("category", "人名"),
        "human",
    )


# ==================== 创建工作流 ====================

workflow = StateGraph(WorkflowState)


workflow.add_node(
    "supervisor",
    supervisor_node,
)

workflow.add_node(
    "human",
    human_naming_node,
)

workflow.add_node(
    "company",
    company_naming_node,
)

workflow.add_node(
    "pet",
    pet_naming_node,
)


# 设置工作流入口
workflow.set_entry_point("supervisor")


# 主管节点根据 category 选择专家
workflow.add_conditional_edges(
    "supervisor",
    route_by_category,
    {
        "human": "human",
        "company": "company",
        "pet": "pet",
    },
)


# 各个专家执行完成后结束
workflow.add_edge("human", END)
workflow.add_edge("company", END)
workflow.add_edge("pet", END)


# ==================== PostgreSQL 持久化记忆 ====================

DB_URI = os.getenv("LANGGRAPH_DB_URI")

if not DB_URI:
    raise RuntimeError(
        "没有读取到 LANGGRAPH_DB_URI，请检查 .env 文件"
    )


# 导入 workflow.py 时只创建连接池对象，不打开连接
connection_pool = AsyncConnectionPool(
    conninfo=DB_URI,
    max_size=10,
    open=False,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0,
        "row_factory": dict_row,
    },
)


# FastAPI 启动后再创建 Saver 和编译工作流
memory: AsyncPostgresSaver | None = None
naming_graph: Any = None


async def start_naming_memory() -> None:
    """
    FastAPI 启动时打开连接池、创建 Saver 并编译工作流。
    """

    global memory
    global naming_graph

    await connection_pool.open()
    await connection_pool.wait()

    # 此处已经处于 Uvicorn 创建的事件循环中
    memory = AsyncPostgresSaver(connection_pool)
    naming_graph = workflow.compile(
        checkpointer=memory
    )

    print("✅ PostgreSQL 记忆连接池启动成功")


async def stop_naming_memory() -> None:
    """FastAPI 关闭时释放 PostgreSQL 连接池。"""

    global memory
    global naming_graph

    naming_graph = None
    memory = None

    await connection_pool.close()

    print("✅ PostgreSQL 记忆连接池已关闭")


# ==================== 第一次生成 ====================

async def generate_names_v2(
    name_info: NameIn,
    user_id: int,
) -> Dict[str, Any]:
    """
    第一次生成名字。

    每次首次生成都会创建新的 thread_id，
    LangGraph 会根据 thread_id 保存本轮状态。
    """

    if naming_graph is None:
        raise RuntimeError(
            "命名工作流尚未初始化，请检查 FastAPI lifespan"
        )

    thread_id = str(uuid.uuid4())

    initial_state: WorkflowState = {
        "user_id": user_id,
        "category": name_info.category,
        "surname": name_info.surname,
        "gender": name_info.gender,
        "length": name_info.length,
        "other": name_info.other,
        "exclude": name_info.exclude,

        # 第一次生成时没有历史记录和修改意见
        "feedback": "",
        "history_names": "",

        "final_output": {},
    }

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    final_state = await naming_graph.ainvoke(
        initial_state,
        config=config,
    )

    return {
        "thread_id": thread_id,
        "names": final_state["final_output"]["names"],
    }


# ==================== 第二次及以后微调 ====================

async def feedback_names(
    feedback_info: FeedbackIn,
    user_id: int,
) -> Dict[str, Any]:
    """
    根据已有 thread_id 唤醒 PostgreSQL 中保存的工作流状态。

    这里只传入新的 feedback 和 category。
    其他字段会根据 thread_id 从历史 checkpoint 中恢复。
    """

    if naming_graph is None:
        raise RuntimeError(
            "命名工作流尚未初始化，请检查 FastAPI lifespan"
        )

    update_state = {
        "feedback": feedback_info.feedback,
        "category": feedback_info.category,
    }

    config = {
        "configurable": {
            "thread_id": feedback_info.thread_id,
        }
    }

    final_state = await naming_graph.ainvoke(
        update_state,
        config=config,
    )

    return {
        "thread_id": feedback_info.thread_id,
        "data": final_state["final_output"],
    }

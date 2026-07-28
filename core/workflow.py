import os
from typing import Any, Dict, List, Literal, TypedDict

from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from langgraph.graph import END, StateGraph
from pydantic import SecretStr

from schemas.name_schemas import NameIn, NameResultSchema
from core.rag_service import retrieve_user_knowledge

load_dotenv()


# 1. 定义工作流中传递的数据结构
class WorkflowState(TypedDict):
    user_id: int  # <--- 新增这一行，为了让节点知道是哪个用户
    category: str
    surname: str
    gender: str
    length: str
    other: str | None
    exclude: List[str]
    final_output: Dict[str, Any]


# 2. 初始化 DeepSeek 大模型
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

if not deepseek_api_key:
    raise RuntimeError("没有读取到 DEEPSEEK_API_KEY，请检查 .env 文件")


llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=SecretStr(deepseek_api_key),
    temperature=1,
)


# 强制大模型按照 NameResultSchema 输出
structured_llm = llm.with_structured_output(NameResultSchema)


# ==================== 节点函数 ====================

async def supervisor_node(
    state: WorkflowState,
) -> Dict[str, Any]:
    """主管节点：后续可扩展意图清洗、日志记录等功能。"""

    return {}


async def human_naming_node(
    state: WorkflowState,
) -> Dict[str, Any]:
    """人名专家节点。"""

    prompt = f"""
你是一位精通汉语言文学与传统文化的命名专家。
请为用户创作富有文化底蕴的人名。

【姓氏】：{state["surname"]}
【性别倾向】：{state["gender"]}
【字数限制】：{state["length"]}
【其他具体要求】：{state["other"] or "无"}
【避讳排除字】：{"、".join(state["exclude"]) or "无"}

原则：
平仄协调，优先从《诗经》《楚辞》或唐诗宋词中汲取灵感。
请给出 5 个候选方案。
"""

    response = await structured_llm.ainvoke(prompt)

    return {
        "final_output": response.model_dump()
    }


async def company_naming_node(state: WorkflowState) -> Dict[str, Any]:
    """企业品牌节点（融合 RAG 增强检索）"""

    # 1. 获取当前用户身份
    current_user_id = state["user_id"]

    # 2. 构造检索词，去 Chroma 里面查该用户上传的专属资料
    search_query = f"{state['other']} 品牌命名规范 行业词汇"
    rag_context = retrieve_user_knowledge(
        query=search_query, user_id=current_user_id
    )

    # 3. 把私有知识喂给大模型
    prompt = f"""你是一位精通商业品牌传播的资深顾问。请创作符合商业规范的公司名。

【用户需求】
行业或核心诉求: {state['other']}
字数限制: {state['length']}
避讳排除字: {'、'.join(state['exclude'])}

【用户的专属私有知识库参考】
{rag_context}

原则：请务必优先参考【用户的专属私有知识库参考】中的规则和词汇。给出 5 个候选方案。"""

    response = await structured_llm.ainvoke(prompt)
    return {"final_output": response.model_dump()}


async def pet_naming_node(
    state: WorkflowState,
) -> Dict[str, Any]:
    """宠物起名节点。"""

    prompt = f"""
你是一位充满创意的宠物达人。
请为用户的宠物起一些富有灵性的名字。

【宠物特征或性格】：{state["other"] or "无"}
【字数限制】：{state["length"]}
【避讳排除字】：{"、".join(state["exclude"]) or "无"}

原则:
亲切好记，富有画面感或软萌感。

请给出5个候选方案。
每个方案必须包含：
- name：宠物名字
- reference：名字的创作来源或命名思路
- moral：名字的含义和寓意
"""

    response = await structured_llm.ainvoke(prompt)

    if response is None:
        raise ValueError("模型没有返回符合 NameResultSchema 的结构化结果")

    return {"final_output": response.model_dump()}


# ==================== 路由逻辑 ====================

def route_by_category(
    state: WorkflowState,
) -> Literal["human", "company", "pet"]:
    """根据前端传来的 category 选择对应节点。"""

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


# 根据类别选择不同的专家节点
workflow.add_conditional_edges(
    "supervisor",
    route_by_category,
    {
        "human": "human",
        "company": "company",
        "pet": "pet",
    },
)


# 每个专家节点执行完毕后结束
workflow.add_edge("human", END)
workflow.add_edge("company", END)
workflow.add_edge("pet", END)


# 编译工作流
naming_graph = workflow.compile()


async def generate_names_v2(
    name_info: NameIn,
    user_id:int
) -> Dict[str, Any]:
    """提供给 Router 调用的统一异步接口。"""

    initial_state: WorkflowState = {
         "user_id": user_id,  # <--- 传进去
        "category": name_info.category,
        "surname": name_info.surname,
        "gender": name_info.gender,
        "length": name_info.length,
        "other": name_info.other,
        "exclude": name_info.exclude,
        "final_output": {},
    }

    final_state = await naming_graph.ainvoke(
        initial_state
    )

    return final_state["final_output"]
import asyncio
from langchain_deepseek import ChatDeepSeek
from langchain_core.prompts import ChatPromptTemplate
from schemas.name_schemas import NameResultSchema,NameIn
from dotenv import load_dotenv
import os

# 读取项目根目录下的 .env 文件
load_dotenv()

# 1. 初始化模型 (温度稍微降一点到 0.5，平衡创意与稳定性)
llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0.5,
    timeout=120
)

# 2. 极致纯净的系统提示词：绝口不提 JSON、格式或工具调用
# 让大模型把 100% 的脑力花在“起名”这件事上
system_prompt = """你是一位精通汉语言文学与传统文化的命名专家。请为用户创作富有文化底蕴的人名。
原则：平仄协调，寓意深远，优先从《诗经》《楚辞》或唐诗宋词中汲取灵感。
请给出 5 个候选方案。"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "【姓氏】:{surname} 【性别】:{gender} 【字数限制】:{length} 【其它要求】:{other} 【避讳字】:{exclude}")
])

# 3. 启用 Tool Calling
structured_llm = llm.with_structured_output(NameResultSchema)
chain = prompt_template | structured_llm


async def generate_names(name_info: NameIn) -> NameResultSchema:
    exclude_str = '、'.join(name_info.exclude) if name_info.exclude else "无"

    # 保持 3 次重试作为物理防线（防网络断开或 502 报错）
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = await chain.ainvoke({
                "surname": name_info.surname,
                "gender": name_info.gender,
                "length": name_info.length,
                "other": name_info.other,
                "exclude": exclude_str
            })

            # 如果成功拿到对象，直接返回
            if result is not None:
                return result

            print(f"⚠️ 第 {attempt + 1} 次模型未按规范输出，正在重试...")

        except Exception as e:
            print(f"❌ 第 {attempt + 1} 次请求遭遇网络异常: {e}，正在重试...")

    raise ValueError("大模型服务器当前较拥挤或未正确响应，生成失败，请稍后重新点击生成。")


async def main():
    name_info = NameIn(
        surname="张",
        gender="女",
        length="两字",
        other="希望名字里带点水的意象",
        exclude=["李", "王"]
    )
    names = await generate_names(name_info)
    print("最终结果:", names)


if __name__ == '__main__':
    asyncio.run(main())
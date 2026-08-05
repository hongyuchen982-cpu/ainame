import asyncio


async def check_com_domain(domain: str) -> str:
    """
    异步工具：向全球 .com 根服务器查询域名是否可用
    """
    # 容错处理：确保查询的是 .com 域名
    if not domain.endswith(".com"):
        if "." not in domain:
            domain += ".com"
        else:
            return "⚠ 仅支持.com校验"

    try:
        # 1. 建立与 whois.verisign-grs.com 的 43 端口异步 TCP 连接
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("whois.verisign-grs.com", 43),
            timeout=3.0,
        )

        writer.write((domain + "\r\n").encode("utf-8"))

        await writer.drain()

        # 3. 读取服务器返回的数据
        response = await asyncio.wait_for(reader.read(), timeout=3.0)

        # 4. 释放连接
        writer.close()
        await writer.wait_closed()

        result = response.decode("utf-8", errors="ignore")

        # 5. 核心逻辑：如果服务器返回 "No match for"，说明没人注册！
        if "No match for" in result:
            return "✅ 未注册 (可买)"
        return "❌ 已被抢注"

    except asyncio.TimeoutError:
        return "⚠ 查询超时"
    except Exception as e:
        return f"⚠ 查询失败: {str(e)}"

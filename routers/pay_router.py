from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.alipaytools import (
    create_alipay,
    get_alipay_gateway,
    get_notify_url,
    get_return_url,
)
from core.authtools import AuthHandler
from dependencies import get_session
from repository.order_repo import OrderRepository
from repository.package_repo import PackageRepository
from schemas.pay_schemas import CreateOrderIn, CreateOrderOut

router = APIRouter(prefix="/pay")
auth_handler = AuthHandler()


@router.post("/create_order", response_model=CreateOrderOut)
async def create_order(
    data: CreateOrderIn,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    package_repo = PackageRepository(session=session)
    order_repo = OrderRepository(session=session)

    # 1. 查询套餐
    package = await package_repo.get_by_id(data.package_id)
    if not package:
        raise HTTPException(status_code=400, detail="套餐不存在或已下架")

    # 2. 创建本地待支付订单
    order = await order_repo.create_order(
        user_id=user_id,
        package=package,
    )

    # 3. 创建支付宝支付链接
    alipay = create_alipay()
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order.order_no,
        total_amount=str(order.amount),
        subject=f"购买{package.name}",
        return_url=get_return_url(),
        notify_url=get_notify_url(),
    )
    pay_url = f"{get_alipay_gateway()}?{order_string}"

    return CreateOrderOut(
        order_no=order.order_no,
        amount=order.amount,
        credit_count=order.credit_count,
        pay_url=pay_url,
    )

from fastapi import Request
from fastapi.responses import HTMLResponse

from decimal import Decimal
from fastapi import Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies import get_session
from core.alipaytools import create_alipay
from repository.order_repo import OrderRepository


@router.get("/success", response_class=HTMLResponse)
async def pay_success(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    支付宝浏览器回跳成功接口 (return_url)。
    注意：
    正常企业项目不建议用它作为最终入账依据。
    但如果 notify_url 暂时调不通，可以先用它完成本地支付成功后的数据库修改。
    """
    # 1. 获取支付宝浏览器跳转回来时携带的参数
    params = dict(request.query_params)

    # 2. 获取订单号
    order_no = params.get("out_trade_no")
    alipay_trade_no = params.get("trade_no", "")
    total_amount = params.get("total_amount")

    if not order_no:
        return """
        <html>
        <head><title>支付结果异常</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h2 style="color: #ff4d4f;">支付结果异常</h2>
            <p>没有获取到订单号 out_trade_no。</p>
        </body>
        </html>
        """

    # 3. 验签
    sign = params.pop("sign", None)
    params.pop("sign_type", None)
    if not sign:
        return """
        <html>
        <head><title>支付结果异常</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h2 style="color: #ff4d4f;">支付结果异常</h2>
            <p>没有获取到支付宝签名。</p>
        </body>
        </html>
        """

    alipay = create_alipay()
    verify_result = alipay.verify(params, sign)
    if not verify_result:
        return """
        <html>
        <head><title>支付结果异常</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h2 style="color: #ff4d4f;">支付结果异常</h2>
            <p>支付宝验签失败，请检查支付宝公钥配置。</p>
        </body>
        </html>
        """

    order_repo = OrderRepository(session=session)

    # 4. 查询本地订单
    order = await order_repo.get_by_order_no(order_no)
    if not order:
        return """
        <html>
        <head><title>支付结果异常</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h2 style="color: #ff4d4f;">支付结果异常</h2>
            <p>订单不存在。</p>
        </body>
        </html>
        """

    # 5. 校验金额，防止有人伪造回跳地址
    if total_amount is not None:
        if Decimal(str(order.amount)) != Decimal(str(total_amount)):
            return """
            <html>
            <head><title>支付结果异常</title></head>
            <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                <h2 style="color: #ff4d4f;">支付结果异常</h2>
                <p>订单金额校验失败。</p>
            </body>
            </html>
            """

    try:
        # 6. 修改数据库：
        # 订单 pending -> paid
        # 增加用户次数
        # 写入次数流水
        order, is_first_success = await order_repo.pay_success(
            order_no=order_no,
            alipay_trade_no=alipay_trade_no,
        )
    except Exception as e:
        return f"""
        <html>
        <head><title>支付处理失败</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h2 style="color: #ff4d4f;">支付处理失败</h2>
            <p>{str(e)}</p>
        </body>
        </html>
        """

    # 7. 返回支付成功页面
    if is_first_success:
        message = f"支付成功，已为您增加 {order.credit_count} 次起名次数。"
    else:
        message = "该订单之前已经处理过，请不要重复刷新页面。"

    return f"""
    <html>
    <head><title>支付成功</title></head>
    <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
        <h2 style="color: #52c41a;">支付成功</h2>
        <p>{message}</p>
        <p>订单号：{order.order_no}</p>
        <p>订单状态：{order.status}</p>
    </body>
    </html>
    """



from schemas.pay_schemas import CreateOrderIn, CreateOrderOut, OrderStatusOut

@router.get("/order/{order_no}", response_model=OrderStatusOut)

async def get_order_status(
    order_no: str,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
    ):
    order_repo = OrderRepository(session=session)
    order = await order_repo.get_by_order_no(order_no)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    # 只能查询自己的订单
    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权查看该订单")
    return order


from decimal import Decimal
from fastapi import Request
from fastapi.responses import PlainTextResponse


from decimal import Decimal
from fastapi import Request, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

# 假设你的依赖项和工具函数引入路径（根据实际项目调整）
# from core.database import get_session
# from utils.alipay import create_alipay
# from repositories.order_repository import OrderRepository


@router.post("/alipay_notify")
async def alipay_notify(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    支付宝异步通知（Webhook）接口。
    注意：此接口必须是公网可访问的 POST 接口，严禁加登录鉴权（Token），
    因为它是支付宝服务器直接发起的后台回调请求。
    """
    # 1. 获取支付宝 POST 过来的表单数据
    form_data = await request.form()
    notify_data = dict(form_data)

    # 2. 取出签名并剔除不参与验签的字段
    sign = notify_data.pop("sign", None)
    notify_data.pop("sign_type", None)  # sign_type 不参与验签

    if not sign:
        return PlainTextResponse("failure")

    # 3. 验证支付宝签名
    alipay = create_alipay()
    verify_result = alipay.verify(notify_data, sign)
    if not verify_result:
        return PlainTextResponse("failure")

    # 4. 获取支付宝通知中的关键数据
    order_no = notify_data.get("out_trade_no")
    alipay_trade_no = notify_data.get("trade_no")
    trade_status = notify_data.get("trade_status")
    total_amount = notify_data.get("total_amount")

    if not order_no:
        return PlainTextResponse("failure")

    # 5. 只处理支付成功状态（TRADE_FINISHED 为交易结束，TRADE_SUCCESS 为支付成功）
    if trade_status not in ["TRADE_SUCCESS", "TRADE_FINISHED"]:
        return PlainTextResponse("success")

    order_repo = OrderRepository(session=session)

    # 6. 查询本地订单
    order = await order_repo.get_by_order_no(order_no)
    if not order:
        return PlainTextResponse("failure")

    # 7. 校验金额，防止客户端恶意篡改金额
    if Decimal(str(order.amount)) != Decimal(str(total_amount)):
        return PlainTextResponse("failure")

    try:
        # 8. 支付成功处理：改订单状态 + 增加次数 + 写流水（内部自带悲观锁与幂等防御）
        await order_repo.pay_success(
            order_no=order_no,
            alipay_trade_no=alipay_trade_no or "",
        )
    except Exception as e:
        # 实际开发中建议打印日志方便排查：print(f"支付回调处理异常: {e}")
        return PlainTextResponse("failure")

    # 9. 必须明确返回 success 字符串，支付宝收到后才会停止重复通知
    return PlainTextResponse("success")

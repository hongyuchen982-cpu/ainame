from decimal import Decimal
from datetime import datetime
from html import escape
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from starlette.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from core.alipaytools import (
    create_alipay,
    get_alipay_gateway,
    get_app_id,
    get_notify_url,
    get_return_url,
    get_seller_id,
)
from core.authtools import AuthHandler
from dependencies import get_session
from repository.order_repo import OrderRepository
from repository.package_repo import PackageRepository
from repository.security_repo import SecurityRepository
from repository.user_repo import UserRepository
from schemas.pay_schemas import (
    AdminOrderOut,
    AdminOrderDetailOut,
    CreateOrderIn,
    CreateOrderOut,
    OrderDetailOut,
    OrderStatusOut,
    RefundOrderIn,
)

router = APIRouter(prefix="/pay")
admin_router = APIRouter(prefix="/admin/orders", tags=["运营后台·订单"])
auth_handler = AuthHandler()


def require_alipay_client():
    try:
        return create_alipay()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="支付宝支付配置不完整") from exc


def build_payment_url(order, alipay, gateway: str, return_url: str, notify_url: str) -> str:
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order.order_no,
        total_amount=str(order.amount),
        subject=f"购买{order.package_name}",
        return_url=return_url,
        notify_url=notify_url,
    )
    return f"{gateway}?{order_string}"


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

    # 2. 先校验支付配置，避免配置错误时留下无效待支付订单。
    alipay = require_alipay_client()
    gateway = get_alipay_gateway()
    return_url = get_return_url()
    notify_url = get_notify_url()
    if not gateway or not return_url or not notify_url:
        raise HTTPException(status_code=503, detail="支付宝支付配置不完整")

    # 3. 创建本地待支付订单
    try:
        order, package = await order_repo.create_order(
            user_id=user_id,
            package_id=package.id,
            client_request_id=data.client_request_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if order.status != "pending":
        raise HTTPException(status_code=409, detail="该幂等请求对应的订单已不能继续支付")
    if order.expires_at and order.expires_at <= datetime.now():
        await order_repo.close_pending(order.order_no, user_id)
        raise HTTPException(status_code=400, detail="订单已经过期，请重新创建")

    # 4. 创建支付宝支付链接
    try:
        pay_url = build_payment_url(order, alipay, gateway, return_url, notify_url)
    except Exception as exc:
        await order_repo.close_pending(order.order_no, user_id)
        raise HTTPException(status_code=502, detail="生成支付宝支付链接失败") from exc

    return CreateOrderOut(
        order_no=order.order_no,
        amount=order.amount,
        credit_count=order.credit_count,
        pay_url=pay_url,
    )

@router.get("/success", response_class=HTMLResponse)
async def pay_success(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    支付宝浏览器回跳成功接口 (return_url)。
    注意：
    此接口只展示异步通知已经写入的订单状态，不负责入账。
    """
    # 1. 获取支付宝浏览器跳转回来时携带的参数
    params = dict(request.query_params)

    # 2. 获取订单号
    order_no = params.get("out_trade_no")
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
        try:
            return_amount_matches = Decimal(str(order.amount)) == Decimal(str(total_amount))
        except Exception:
            return_amount_matches = False
        if not return_amount_matches:
            return """
            <html>
            <head><title>支付结果异常</title></head>
            <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                <h2 style="color: #ff4d4f;">支付结果异常</h2>
                <p>订单金额校验失败。</p>
            </body>
            </html>
            """

    # 浏览器回跳只展示状态，绝不作为到账依据；到账仅由异步通知处理。
    if order.status == "paid":
        heading = "支付成功"
        heading_color = "#52c41a"
        message = f"支付成功，已为您增加 {order.credit_count} 次起名次数。"
    else:
        heading = "支付确认中"
        heading_color = "#d48806"
        message = "支付结果正在确认，请稍后回到网站查询订单状态。"

    return f"""
    <html>
        <head><title>{escape(heading)}</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
        <h2 style="color: {heading_color};">{escape(heading)}</h2>
        <p>{escape(message)}</p>
        <p>订单号：{escape(order.order_no)}</p>
        <p>订单状态：{escape(order.status)}</p>
    </body>
    </html>
    """
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


@router.get("/orders", response_model=list[OrderStatusOut])
async def list_my_orders(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    return await OrderRepository(session).list_for_user(
        user_id, limit=limit, offset=offset
    )


@router.get("/orders/{order_no}/detail", response_model=OrderDetailOut)
async def get_order_detail(
    order_no: str,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = OrderRepository(session)
    order = await repo.get_for_user(order_no, user_id)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    transactions = await repo.list_transactions(order.id)
    data = {column.name: getattr(order, column.name) for column in order.__table__.columns}
    data["transactions"] = transactions
    return data


@router.post("/orders/{order_no}/pay", response_model=CreateOrderOut)
async def continue_order_payment(
    order_no: str,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    order = await OrderRepository(session).get_for_user(order_no, user_id)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="只有待支付订单可以继续支付")
    if order.expires_at and order.expires_at <= datetime.now():
        await OrderRepository(session).close_pending(order_no, user_id)
        raise HTTPException(status_code=400, detail="订单已经过期，请重新创建")
    alipay = require_alipay_client()
    gateway = get_alipay_gateway()
    return_url = get_return_url()
    notify_url = get_notify_url()
    if not gateway or not return_url or not notify_url:
        raise HTTPException(status_code=503, detail="支付宝支付配置不完整")
    try:
        pay_url = build_payment_url(order, alipay, gateway, return_url, notify_url)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="生成支付宝支付链接失败") from exc
    return CreateOrderOut(
        order_no=order.order_no,
        amount=order.amount,
        credit_count=order.credit_count,
        pay_url=pay_url,
    )


@router.post("/orders/{order_no}/close", response_model=OrderStatusOut)
async def close_my_order(
    order_no: str,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = OrderRepository(session)
    order = await repo.get_for_user(order_no, user_id)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status == "closed":
        return order
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="只有待支付订单可以关闭")
    try:
        alipay = require_alipay_client()
        result = await run_in_threadpool(
            alipay.api_alipay_trade_close, out_trade_no=order_no
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="支付宝关闭订单失败") from exc
    code = str(result.get("code", ""))
    sub_code = str(result.get("sub_code", ""))
    if code != "10000" and sub_code != "ACQ.TRADE_NOT_EXIST":
        raise HTTPException(status_code=409, detail=result.get("sub_msg") or "订单当前不能关闭")
    try:
        return await repo.close_pending(order_no, user_id)
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/orders/{order_no}/sync", response_model=OrderStatusOut)
async def sync_order_status(
    order_no: str,
    user_id: int = Depends(auth_handler.auth_access_dependency),
    session: AsyncSession = Depends(get_session),
):
    repo = OrderRepository(session)
    order = await repo.get_for_user(order_no, user_id)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending":
        return order
    try:
        alipay = require_alipay_client()
        result = await run_in_threadpool(
            alipay.api_alipay_trade_query, out_trade_no=order_no
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="支付宝订单同步失败") from exc
    if str(result.get("code", "")) != "10000":
        if str(result.get("sub_code", "")) == "ACQ.TRADE_NOT_EXIST":
            return order
        raise HTTPException(status_code=502, detail=result.get("sub_msg") or "支付宝订单查询失败")
    if result.get("trade_status") in {"TRADE_SUCCESS", "TRADE_FINISHED"}:
        try:
            if Decimal(str(result.get("total_amount"))) != Decimal(str(order.amount)):
                raise HTTPException(status_code=409, detail="支付宝订单金额不一致")
        except (ValueError, TypeError):
            raise HTTPException(status_code=409, detail="支付宝订单金额无效")
        order, _ = await repo.pay_success(
            order_no,
            str(result.get("trade_no", "")),
            json.dumps(result, ensure_ascii=False),
        )
    return order


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
    alipay = require_alipay_client()
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

    expected_app_id = get_app_id()
    if expected_app_id and notify_data.get("app_id") != expected_app_id:
        return PlainTextResponse("failure")
    expected_seller_id = get_seller_id()
    if expected_seller_id and notify_data.get("seller_id") != expected_seller_id:
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
    try:
        amount_matches = (
            total_amount is not None
            and Decimal(str(order.amount)) == Decimal(str(total_amount))
        )
    except Exception:
        amount_matches = False
    if not amount_matches:
        return PlainTextResponse("failure")

    try:
        # 8. 支付成功处理：改订单状态 + 增加次数 + 写流水（内部自带悲观锁与幂等防御）
        await order_repo.pay_success(
            order_no=order_no,
            alipay_trade_no=alipay_trade_no or "",
            detail=json.dumps(notify_data, ensure_ascii=False),
        )
    except Exception:
        # 实际开发中建议打印日志方便排查：print(f"支付回调处理异常: {e}")
        return PlainTextResponse("failure")

    # 9. 必须明确返回 success 字符串，支付宝收到后才会停止重复通知
    return PlainTextResponse("success")


@admin_router.get("", response_model=list[AdminOrderOut])
async def admin_list_orders(
    status: Literal["pending", "paid", "closed", "refunding", "refunded"] | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin_id: int = Depends(auth_handler.require_permissions("orders.manage")),
    session: AsyncSession = Depends(get_session),
):
    rows = await OrderRepository(session).list_all(
        status=status, limit=limit, offset=offset
    )
    return [
        {
            **{column.name: getattr(order, column.name) for column in order.__table__.columns},
            "email": user.email,
            "username": user.username,
        }
        for order, user in rows
    ]


@admin_router.get("/{order_no}", response_model=AdminOrderDetailOut)
async def admin_order_detail(
    order_no: str,
    admin_id: int = Depends(auth_handler.require_permissions("orders.manage")),
    session: AsyncSession = Depends(get_session),
):
    repo = OrderRepository(session)
    order = await repo.get_by_order_no(order_no)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    user = await UserRepository(session).get_by_id(order.user_id)
    transactions = await repo.list_transactions(order.id)
    return {
        **{column.name: getattr(order, column.name) for column in order.__table__.columns},
        "email": user.email,
        "username": user.username,
        "transactions": transactions,
    }


@admin_router.post("/{order_no}/close", response_model=OrderStatusOut)
async def admin_close_order(
    order_no: str,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("orders.manage")),
    session: AsyncSession = Depends(get_session),
):
    repo = OrderRepository(session)
    order = await repo.get_by_order_no(order_no)
    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="只有待支付订单可以关闭")
    try:
        alipay = require_alipay_client()
        result = await run_in_threadpool(
            alipay.api_alipay_trade_close, out_trade_no=order_no
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="支付宝关闭订单失败") from exc
    if str(result.get("code", "")) != "10000" and str(result.get("sub_code", "")) != "ACQ.TRADE_NOT_EXIST":
        raise HTTPException(status_code=409, detail=result.get("sub_msg") or "订单当前不能关闭")
    try:
        order = await repo.close_pending(order_no)
    except (LookupError, ValueError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    async with session.begin():
        await SecurityRepository(session).audit_in_transaction(
            admin_user_id=admin_id,
            action="order.close",
            target_type="order",
            target_id=order_no,
            detail="{}",
            ip_address=request.client.host if request.client else "unknown",
        )
    return order


@admin_router.post("/{order_no}/refund", response_model=OrderStatusOut)
async def refund_order(
    order_no: str,
    data: RefundOrderIn,
    request: Request,
    admin_id: int = Depends(auth_handler.require_permissions("orders.refund")),
    session: AsyncSession = Depends(get_session),
):
    repo = OrderRepository(session)
    # 必须在预扣用户权益之前确认支付宝客户端配置可用。
    alipay = require_alipay_client()
    try:
        order, transaction, should_call_provider = await repo.begin_refund(
            order_no, data.request_no, data.reason
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if transaction.status == "success":
        return order
    if transaction.status == "failed":
        raise HTTPException(status_code=409, detail="该退款请求已经失败，请使用新的请求号重试")
    if not should_call_provider:
        return order

    try:
        result = await run_in_threadpool(
            alipay.api_alipay_trade_refund,
            refund_amount=str(order.amount),
            out_trade_no=order.order_no,
            out_request_no=data.request_no,
            refund_reason=data.reason,
        )
    except Exception as exc:
        # 网络超时无法判断支付宝是否已经受理，保留 refunding/pending，
        # 管理员使用相同 request_no 重试即可安全对账。
        raise HTTPException(status_code=502, detail="支付宝退款状态未知，请使用同一请求号重试") from exc

    detail = json.dumps(result, ensure_ascii=False)
    if str(result.get("code", "")) != "10000":
        await repo.fail_refund(order_no, data.request_no, detail)
        raise HTTPException(status_code=502, detail=result.get("sub_msg") or "支付宝退款失败")
    order = await repo.complete_refund(order_no, data.request_no, detail)
    async with session.begin():
        await SecurityRepository(session).audit_in_transaction(
            admin_user_id=admin_id,
            action="order.refund",
            target_type="order",
            target_id=order_no,
            detail=data.model_dump_json(),
            ip_address=request.client.host if request.client else "unknown",
        )
    return order

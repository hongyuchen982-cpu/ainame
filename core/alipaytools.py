import os
import textwrap
from alipay import AliPay
from dotenv import load_dotenv

load_dotenv()

def format_private_key(key):
    key = key.replace(" ", "").replace("\n", "")
    key = "\n".join(textwrap.wrap(key, 64))

    return f"-----BEGIN RSA PRIVATE KEY-----\n{key}\n-----END RSA PRIVATE KEY-----"

def format_public_key(key):

    key = key.replace(" ", "").replace("\n", "")
    key = "\n".join(textwrap.wrap(key, 64))
    return f"-----BEGIN PUBLIC KEY-----\n{key}\n-----END PUBLIC KEY-----"

def create_alipay():
    app_id = os.getenv("ALIPAY_APP_ID")
    private_key = os.getenv("ALIPAY_APP_PRIVATE_KEY")
    public_key = os.getenv("ALIPAY_PUBLIC_KEY")
    if not app_id or not private_key or not public_key:
        raise RuntimeError("支付宝配置不完整")
    return AliPay(
    appid=app_id,
    app_notify_url=os.getenv("ALIPAY_NOTIFY_URL"),
    app_private_key_string=format_private_key(private_key),
    alipay_public_key_string=format_public_key(public_key),
    sign_type="RSA2",
    debug=os.getenv("ALIPAY_DEBUG", "false").lower() == "true",
    )

def get_alipay_gateway():

    return os.getenv("ALIPAY_GATEWAY")

def get_return_url():
    return os.getenv("ALIPAY_RETURN_URL")
def get_notify_url():
    return os.getenv("ALIPAY_NOTIFY_URL")


def get_app_id():
    return os.getenv("ALIPAY_APP_ID", "")


def get_seller_id():
    return os.getenv("ALIPAY_SELLER_ID", "")

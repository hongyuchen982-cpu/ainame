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

    return AliPay(
    appid=os.getenv("ALIPAY_APP_ID"),
    app_notify_url=os.getenv("ALIPAY_NOTIFY_URL"),
    app_private_key_string=format_private_key(os.getenv("ALIPAY_APP_PRIVATE_KEY")),
    alipay_public_key_string=format_public_key(os.getenv("ALIPAY_PUBLIC_KEY"
    )),
    sign_type="RSA2",
    debug=True
    )

def get_alipay_gateway():

    return os.getenv("ALIPAY_GATEWAY")

def get_return_url():
    return os.getenv("ALIPAY_RETURN_URL")
def get_notify_url():
    return os.getenv("ALIPAY_NOTIFY_URL")
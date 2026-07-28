from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv
import os
load_dotenv()
DB_URI = os.getenv("DB_URI")
engine = create_async_engine(
    DB_URI,
# 将输出所有执行SQL的日志（默认是关闭的）
    echo=True,
# 连接池大小（默认是5个）
    pool_size=10,
# 允许连接池最大的连接数（默认是10个）
    max_overflow=20,
# 获得连接超时时间（默认是30s）
    pool_timeout=10,
# 连接回收时间（默认是-1，代表永不回收）
    pool_recycle=3600,
# 连接前是否预检查（默认是False）
    pool_pre_ping=True,
)
AsyncSessionFactory = async_sessionmaker(
bind=engine,     
autoflush=True,   
# flush，SQLAlchemy 会自动把内存里的修改同步到数据库事务中
expire_on_commit=False  # commit() 后仍然可以访问对象属性
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
# 定义命名约定的Base类
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
    # ix: index，索引
    "ix": "ix_%(column_0_label)s",
    # un: unique，唯一约束
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    # ck: Check，检查约束
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    # fk: Foreign Key，外键约束
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    # pk: Primary Key，主键约束
    "pk": "pk_%(table_name)s"
    })

from . import user


from . import user
from . import user_credit

from . import package
from . import user_order
from . import  Base
from sqlalchemy.orm import mapped_column,Mapped
from sqlalchemy import Integer, String, DateTime
from pwdlib import PasswordHash
from datetime import datetime

password_hash = PasswordHash.recommended()

class User(Base):
    __tablename__ = 'user'
    id:Mapped[int] = mapped_column(Integer, primary_key=True,autoincrement=True)
    email:Mapped[str] = mapped_column(String(100),unique=True)
    username:Mapped[str] = mapped_column(String(100))
    _password:Mapped[str] = mapped_column(String(200))
    avatar_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    # 触发时机：当你通过类实例化创建一个新对象时
    # *args.能接收任意多个、不带名字的值,**kwargs 能接收任意多个、带名字的值
    def __init__(self, *args,**kwargs):
        
        password = kwargs.pop('password',None)
        super().__init__(*args,**kwargs)
        if password:
        # self.password 会自动调用@password.setter 下面的函数，实现加密，自动存到 
            self.password = password
            # 触发时机：当你以属性访问方式读取 user.password 时
    @property
    def password(self):
        return self._password
    @password.setter
    def password(self,password):
        self._password =  password_hash.hash(password)
    def check_password(self,password):
        return password_hash.verify(password,self._password)

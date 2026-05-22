# 1. 依赖导入
import enum
from typing import List, Optional
from pwdlib import PasswordHash
from sqlalchemy import String, Boolean, Enum as SEnum, ForeignKey, Table, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import BaseModel, Base

# 这是 HR 系统的核心用户数据模型，定义了用户、部门和钉钉集成的数据库结构。

# 2. 密码加密器初始化
"""
作用：创建密码哈希器实例，用于密码的加密和验证。
设计考量：
PasswordHash.recommended() 自动选择当前安全的哈希算法（如 Argon2）
相比手动使用 bcrypt 等库，更安全且易于维护
自动处理盐值生成和参数选择
"""
password_hasher = PasswordHash.recommended()


# 3. 用户状态枚举
class UserStatus(enum.Enum):
    """
    作用：定义用户的状态，用于权限控制和业务逻辑判断。
    优势：
    类型安全：避免使用魔法字符串
    自动验证：数据库层面限制只能是这三个值
    代码可读性高：user.status == UserStatus.ACTIVE
    """
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    RESIGNED = "RESIGNED"


# 4. 多对多关联表
# 关联表：HR管理的部门
"""
作用：建立 HR 用户与部门之间的多对多关系（一个HR可以管理多个部门，一个部门可以被多个HR管理）。
设计原因：
SQLAlchemy 中多对多关系需要显式定义中间表
中间表只存储关联关系，不包含业务逻辑
复合主键确保同一关联不会重复
"""
hr_managed_departments = Table(
    "hr_managed_departments",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("department_id", ForeignKey("departments.id"), primary_key=True),
)


# 5. 用户模型
class UserModel(BaseModel):
    __tablename__ = "users"
    # 基础字段
    """
    字段	            设计意图
    username	        登录用户名，唯一索引加速查询
    _password	        私有字段存储哈希密码，禁止直接访问
    email/phone_number	联系方式，支持唯一约束防止重复
    realname	        用户真实姓名
    avatar	            头像URL，可选字段
    department_id	    所属部门，允许为空（如超级管理员）
    status	            用户状态，默认激活
    is_hr	            是否为HR角色
    is_superuser	    是否为超级管理员    
    """
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    _password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)
    realname: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String(255))

    # 外键关联
    department_id: Mapped[Optional[str]] = mapped_column(ForeignKey("departments.id"))

    # 状态和权限
    status: Mapped[UserStatus] = mapped_column(SEnum(UserStatus), default=UserStatus.ACTIVE)
    is_hr: Mapped[bool] = mapped_column(Boolean, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    # 关系定义
    """
    关系	                类型	           	说明
    department	            一对多	用户所属部门（一个部门有多个成员）
    managed_departments	    多对多	HR管理的部门（通过中间表）
    dingding_user	        一对一	关联的钉钉用户信息
    lazy="joined"	                查询用户时立即加载部门信息，避免N+1查询问题。
    """
    department: Mapped[Optional["DepartmentModel"]] = relationship(back_populates="members",
                                                                   foreign_keys=[department_id], lazy="joined")
    managed_departments: Mapped[List["DepartmentModel"]] = relationship(
        secondary=hr_managed_departments, back_populates="managing_hrs"
    )
    dingding_user: Mapped["DingdingUserModel"] = relationship(back_populates="user", uselist=False)

    # 密码处理机制
    """
    安全设计：
    机制	                说明
    _password 私有	        强制通过属性访问，防止直接操作
    构造函数支持 password	创建用户时可直接传原始密码
    @password.setter	    修改密码时自动哈希
    check_password()	    安全的密码验证方法
    """

    def __init__(self, **kwargs):
        # 支持通过 password 参数传入原始密码
        if "password" in kwargs:
            raw_password = kwargs.pop("password")
            kwargs["_password"] = password_hasher.hash(raw_password)
        super().__init__(**kwargs)

    @property
    def password(self):
        return self._password  # 返回哈希值

    @password.setter
    def password(self, password):
        self._password = password_hasher.hash(password)  # 设置时自动哈希

    def check_password(self, password):
        return password_hasher.verify(password, self._password)  # 验证密码


# 6. 部门模型
class DepartmentModel(BaseModel):
    __tablename__ = "departments"

    """
    关系说明：
    members：部门成员（反向引用）
    managing_hrs：管理该部门的HR列表（多对多）
    """
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    members: Mapped[List["UserModel"]] = relationship(back_populates="department")
    managing_hrs: Mapped[List["UserModel"]] = relationship(
        secondary=hr_managed_departments, back_populates="managed_departments"
    )


# 7. 钉钉用户模型
class DingdingUserModel(BaseModel):
    __tablename__ = "dingding_user"
    """
    钉钉集成字段：
    字段	                    用途
    union_id	                钉钉开放平台用户唯一标识
    open_id	                    企业内用户唯一标识
    access_token	            访问令牌（2小时过期）
    refresh_token	            刷新令牌（30天过期）
    refresh_token_expire_at	    刷新令牌过期时间戳
    设计考量：
    一对一关联用户模型
    存储OAuth令牌用于后续API调用
    时间戳存储便于判断令牌是否过期
    """
    nick: Mapped[str] = mapped_column(String(100), nullable=False)
    union_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    open_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    mobile: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    # access_token默认过期时间是2小时
    access_token: Mapped[str] = mapped_column(String(255), nullable=False)
    # refresh_token默认过期时间是30天
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=False)
    # refresh_token的过期时间，保存的是时间戳
    refresh_token_expire_at: Mapped[int] = mapped_column(Integer, nullable=False)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["UserModel"] = relationship(back_populates="dingding_user")

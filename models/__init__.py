# MetaData SQLAlchemy 的元数据对象，用于管理数据库表的约束命名约定
from sqlalchemy import MetaData
# create_async_engine 创建异步数据库引擎（支持异步操作）
from sqlalchemy.ext.asyncio import create_async_engine
# sessionmaker 会话工厂，用于创建数据库会话 DeclarativeBase SQLAlchemy 2.0 的声明式基类
from sqlalchemy.orm import sessionmaker, DeclarativeBase
# AsyncSession 异步会话类，用于执行异步数据库操作
from sqlalchemy.ext.asyncio import AsyncSession
# shortuuid.uuid 生成短UUID（比标准UUID更短）
from shortuuid import uuid
from datetime import datetime
# Mapped, mapped_column	SQLAlchemy 2.0 的类型注解方式
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String
from settings import settings

# 这是 HR 系统的数据库模型基础层，负责配置数据库连接、会话管理和基础模型定义。

# 创建异步数据库引擎
engine = create_async_engine(
    # 从配置读取数据库连接URL
    settings.DATABASE_URL,
    # 将输出所有执行SQL的日志（默认是关闭的）
    echo=False,
    # 连接池大小（默认是5个）
    pool_size=10,
    # 允许连接池最大的连接数（默认是10个）
    max_overflow=20,
    # 获得连接超时时间（默认是30s）
    pool_timeout=10,
    # 连接回收时间（默认是-1，代表永不回收）
    pool_recycle=3600,
    # 连接前是否预检查（默认为False）
    pool_pre_ping=True,
)

# 创建异步会话工厂
"""
工厂模式的重要性
如果没有工厂模式会怎样？
错误的方式 - 直接使用单个实例
如果这样做，所有HTTP请求会共享同一个数据库会话
这会导致严重的并发问题和数据污染

工厂模式的好处：
并发安全：每个HTTP请求获得独立的会话实例
资源管理：每个会话可以独立开启和关闭
事务隔离：每个请求的事务相互独立
内存管理：避免会话实例累积导致内存泄漏
"""
AsyncSessionFactory = sessionmaker(
    # 绑定到异步引擎 Engine或者其子类对象（这里是AsyncEngine）
    bind=engine,
    # 使用异步会话类 Session类的代替（默认是Session类）
    class_=AsyncSession,
    # 是否在查找之前执行flush操作（默认是True）
    autoflush=True,  # 确保查询前将待保存的对象写入数据库
    # 是否在执行commit操作后Session就过期（默认是True）
    expire_on_commit=False  # commit后对象仍可访问，提升用户体验
)


# 创建 Declarative Base
# 定义命名约定的Base类
class Base(DeclarativeBase):
    """
    为什么需要命名约定？
    默认行为：SQLAlchemy 会生成随机命名的约束（如 ix_12345）
    问题：数据库迁移时难以识别约束，调试困难
    解决方案：统一命名规则，便于维护和迁移
    迁移友好：数据库迁移工具（如Alembic）能正确识别约束
    团队协作：统一的命名规范便于团队成员理解
    """
    metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",  # 索引命名规则
        "uq": "uq_%(table_name)s_%(column_0_name)s",  # 唯一约束
        "ck": "ck_%(table_name)s_%(constraint_name)s",  # 检查约束
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # 外键
        "pk": "pk_%(table_name)s",  # 主键
    })


# 定义抽象基础模型 BaseModel
class BaseModel(Base):
    """
    设计意图：
    字段	    作用	    设计考量
    id	        主键	    使用短UUID而非自增ID，避免ID泄露业务数据
    created_at	创建时间	    记录记录创建时刻
    updated_at	更新时间	    onupdate确保每次更新自动刷新
    """
    __abstract__ = True

    """
    Mapped 是 SQLAlchemy 2.0 引入的类型提示机制，用于在 ORM 模型中明确指定列的类型。
    具体功能：
    类型注解：Mapped[str] 表明这个字段在 Python 中是一个字符串类型
    ORM 映射：告诉 SQLAlchemy 这是一个数据库列的映射
    静态分析支持：IDE 和类型检查器可以更好地理解代码结构
    更好的开发体验：提供更好的代码补全和错误检测
    """
    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: uuid())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


# 这和 Alembic（数据库迁移工具）密切相关
# 作用：确保 user.py 中的所有模型类被加载并注册到 SQLAlchemy 的 Base.metadata 中。
"""
Base.metadata 是一个全局注册表，记录所有继承自 Base 的模型类
当你定义 class UserModel(BaseModel) 时，UserModel 会自动注册到 Base.metadata
但这只有在模块被导入时才会发生！

为什么 Alembic 需要这个？
Alembic 是 SQLAlchemy 的数据库迁移工具，它需要：
扫描所有模型：了解数据库中有哪些表和字段
对比差异：比较当前模型和数据库schema的差异
生成迁移脚本：根据差异自动生成 ALTER TABLE 等 SQL
如果不导入 user 模块会怎样？
结果：Alembic 认为数据库中没有任何表，会尝试创建所有表（即使它们已经存在）。

导入位置的讲究,为什么放在文件末尾？
1. 避免循环导入
BaseModel 在第71行定义，user.py 中引用了 BaseModel
如果在顶部导入 user，会导致：
models/__init__.py → user.py → models/__init__.py（还没定义 BaseModel）
2. 确保 BaseModel 先被定义
user.py 中的模型继承自 BaseModel
必须等 BaseModel 定义完成后才能导入 user

完整的加载流程
1. 导入 models 模块
from models import Base
2. 执行 models/__init__.py
    - 定义 Base 类
    - 定义 BaseModel 类  
    - 最后执行 from . import user
3. 执行 user.py
    - 定义 UserModel(BaseModel)
    - UserModel 自动注册到 Base.metadata
4. Base.metadata 现在包含所有表定义
    - users 表
    - departments 表
    - dingding_user 表
    - hr_managed_departments 关联表
"""
from . import user
from . import positions
from . import interview
from . import candidate

"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HR 系统数据库                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐      ┌──────────────────────┐      ┌──────────────┐      │
│  │ departments  │◄─────│     users            │─────►│dingding_user │      │
│  │──────────────│      │──────────────────────│      │──────────────│      │
│  │ id (PK)      │      │ id (PK)              │      │ id (PK)      │      │
│  │ name         │      │ department_id (FK)   │      │ user_id (FK) │      │
│  │ description  │      │ status               │      │ union_id     │      │
│  └──────────────┘      │ is_hr                │      │ open_id      │      │
│         │              │ is_superuser         │      │ mobile       │      │
│         │              └──────────────────────┘      │ access_token │      │
│         │                           │                └──────────────┘      │
│         │                           │                                      │
│         │                           ▼                                      │
│         │              ┌──────────────────────┐                            │
│         │              │  hr_managed_departments                            │
│         │              │  (M:N关联表)          │                            │
│         └─────────────►│  user_id (FK)        │                            │
│                        │  department_id (FK)  │                            │
│                        └──────────────────────┘                            │
│                                                                             │
│  ┌──────────────┐      ┌──────────────────────┐      ┌──────────────┐      │
│  │  positions   │◄─────│     candidates       │─────►│interviews   │      │
│  │──────────────│      │──────────────────────│      │──────────────│      │
│  │ id (PK)      │      │ id (PK)              │      │ id (PK)      │      │
│  │ department_id│      │ position_id (FK)     │      │ candidate_id │      │
│  │ creator_id   │      │ resume_id (FK)       │      │ interviewer_ │      │
│  │ title        │      │ creator_id (FK)      │      │   id (FK)    │      │
│  │ requirements │      │ status               │      │ result       │      │
│  └──────────────┘      └──────────────────────┘      └──────────────┘      │
│         │                           │                                      │
│         │                           ▼                                      │
│         │              ┌──────────────────────┐                            │
│         │              │ candidate_ai_scores  │                            │
│         │              │──────────────────────│                            │
│         │              │ id (PK)              │                            │
│         │              │ candidate_id (FK)    │                            │
│         │              │ overall_score        │                            │
│         │              │ summary              │                            │
│         │              │ strengths (JSON)     │                            │
│         │              │ weaknesses (JSON)    │                            │
│         │              └──────────────────────┘                            │
│         │                                                                 │
│         ▼                                                                 │
│  ┌──────────────┐                                                          │
│  │   resumes    │                                                          │
│  │──────────────│                                                          │
│  │ id (PK)      │                                                          │
│  │ file_path    │                                                          │
│  │ uploader_id  │                                                          │
│  └──────────────┘                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""
"""
核心业务流程
用户注册/入职 ──► 创建用户记录 ──► 分配部门
                                    │
                                    ▼
                           HR创建职位 ──► 发布招聘
                                           │
                                           ▼
                              候选人投递简历 ──► AI筛选
                                                   │
                                                   ├─ 通过 ──► 安排面试 ──► 面试通过 ──► 入职
                                                   │
                                                   └─ 失败 ──► 拒绝候选人
"""

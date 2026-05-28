from models import AsyncSessionFactory, AsyncSession
from core.auth import AuthHandler
from fastapi import Depends, HTTPException, status

from models.user import UserModel, UserStatus
from repository.user_repo import UserRepo


async def get_session_instance():
    """
    FastAPI 依赖注入函数，用于为每个 HTTP 请求提供一个独立的异步数据库会话（Session），
    并确保请求结束后自动释放会话资源。

    实际运行示例
    当两个用户同时登录时：
    用户A请求：
    调用get_session_instance()
    AsyncSessionFactory()创建session_A实例
    session_A用于用户A的数据库操作
    请求结束，session_A关闭
    用户B请求（同时发生）：

    调用get_session_instance()
    AsyncSessionFactory()创建session_B实例（全新实例）
    session_B用于用户B的数据库操作
    请求结束，session_B关闭
    结果：两个请求完全隔离，互不影响

    为什么只在dependencies中导入
    AsyncSessionFactory只在创建会话时需要，即在依赖注入函数中
    其他地方只需要具体的AsyncSession实例来执行操作
    这种设计遵循了关注点分离原则：工厂负责创建，实例负责操作
    总结：AsyncSessionFactory是会话创建者，AsyncSession是会话使用者。
    工厂模式确保了每个HTTP请求都能获得独立的数据库会话，这是实现高并发、线程安全的关键设计。
    """
    # 使用工厂创建新实例从AsyncSessionFactory获取一个异步数据库会话
    session: AsyncSession = AsyncSessionFactory()
    try:
        yield session  # 返回具体的会话实例，用于路由函数中的数据库操作
    finally:
        await session.close()


# 创建一个全局共享的AuthHandler实例
"""避免重复创建认证处理器对象，节省内存资源
确保在整个应用生命周期中使用同一个认证处理器
AuthHandler本身使用单例模式实现，这里进一步确保只有一个实例"""
auth_handler = AuthHandler()


# 依赖注入函数
async def get_auth_handler():
    """
    目的：为FastAPI提供一个依赖注入函数
    工作机制：
    当路由函数需要AuthHandler实例时，FastAPI会自动调用此函数
    函数返回预先创建的auth_handler单例实例
    支持异步操作，符合FastAPI的异步特性
    """
    return auth_handler


# 使用依赖注入从JWT令牌中提取用户ID
def get_user_id(
        iss: str = Depends(auth_handler.auth_access_dependency)
) -> str:
    """
    通过 auth_handler.auth_access_dependency 验证访问令牌的有效性
    返回：解码后的用户标识符(iss)
    """
    return iss


async def get_current_user(
        user_id: str = Depends(get_user_id),
        session: AsyncSession = Depends(get_session_instance)
) -> UserModel:
    async with session.begin():
        user_repo = UserRepo(session)
        user: UserModel = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="该用户不存在！")
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="该账号不可用，请联系管理员！")
        return user


# 超级管理员访问权限
async def get_super_user(
        current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """
    想要针对某个视图函数进行访问限制，我们通常会使用装饰器来实现，
    而在FastAPI项目中，则通常使用依赖注入的形式实现，
    """
    if current_user.is_superuser:
        return current_user
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足，无法访问！")

from models import AsyncSessionFactory, AsyncSession
from core.auth import AuthHandler


async def get_session_instance():
    """
    FastAPI 依赖注入函数，用于为每个 HTTP 请求提供一个独立的异步数据库会话（Session），
    并确保请求结束后自动释放会话资源。
    """
    session: AsyncSession = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()


auth_handler = AuthHandler()


async def get_auth_handler():
    return auth_handler

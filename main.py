from fastapi import FastAPI
from routers.user_router import router as user_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from redis import asyncio as aioredis
from settings import settings
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache import FastAPICache

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,  # FastAPI 提供的跨域中间件类
    allow_origins=["*"],  # 允许的来源域名列表，"*" 表示允许所有域名
    allow_credentials=True,  # 是否允许携带认证凭证（如 Cookie、Authorization）
    allow_methods=["*"],  # 允许的 HTTP 方法，"*" 表示允许所有方法（GET、POST、PUT、DELETE 等）
    allow_headers=["*"],  # 允许的请求头，"*" 表示允许所有自定义请求头
)


# 生命周期管理器函数，用于在FastAPI应用程序启动和关闭时执行特定的操作
@asynccontextmanager
async def lifespan(_: FastAPI):
    # 1. yield之前的代码，是程序运行前执行的
    """
    Redis连接初始化：使用配置文件中的主机和端口信息创建Redis客户端连接
        使用 aioredis.from_url() 方法建立异步Redis连接
        设置UTF-8编码和响应解码选项
    缓存后端设置：创建Redis缓存后端实例
    缓存初始化：使用 FastAPICache.init() 初始化缓存系统，并设置缓存前缀为 "fastapi-cache"
    """
    redis_client = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        encoding="utf-8",
        decode_responses=True,
    )
    cache_backend = RedisBackend(redis_client)
    FastAPICache.init(cache_backend, prefix="fastapi-cache")
    yield
    # 2. yield之后的代码，是程序即将退出之前执行的
    # 资源清理：当应用程序关闭时，自动关闭Redis连接以释放资源
    await redis_client.close()


app = FastAPI(lifespan=lifespan)

app.include_router(user_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

from fastapi import FastAPI
from routers.user_router import router as user_router
# from . import models
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 允许跨域
app.add_middleware(
    CORSMiddleware,  # FastAPI 提供的跨域中间件类
    allow_origins=["*"],  # 允许的来源域名列表，"*" 表示允许所有域名
    allow_credentials=True,  # 是否允许携带认证凭证（如 Cookie、Authorization）
    allow_methods=["*"],  # 允许的 HTTP 方法，"*" 表示允许所有方法（GET、POST、PUT、DELETE 等）
    allow_headers=["*"],  # 允许的请求头，"*" 表示允许所有自定义请求头
)

app.include_router(user_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

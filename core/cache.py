from core.single import SingletonMeta
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from schemas.cache_schema import InviteInfoSchema, DingTalkTokenInfoSchema
from settings import settings


# 基于Redis的缓存管理类
# 使用单例模式，确保整个应用程序中只有一个缓存实例
class HRCache(metaclass=SingletonMeta):
    # 定义邀请相关的缓存键前缀
    invite_prefix = "invite:"
    # 定义钉钉相关的缓存键前缀
    dingtalk_prefix = "dingtalk:"

    # 初始化缓存后端，获取FastAPI缓存的Redis后端实例
    def __init__(self):
        self.cache_backend: RedisBackend = FastAPICache.get_backend()

    # 设置缓存键值对，可选过期时间
    async def set(self, key, value, ex: int):
        await self.cache_backend.set(key, value, expire=ex if ex else None)

    # 获取缓存键对应的值
    async def get(self, key):
        value = await self.cache_backend.get(key)
        return value

    # 删除缓存键对应的值
    async def delete(self, key):
        await self.cache_backend.clear(key)

    # 设置邀请信息缓存，过期时间为配置文件中的默认值
    async def set_invite_info(self, invite_info: InviteInfoSchema):
        # 使用邮箱作为键的一部分构建唯一缓存键
        key = f"{self.invite_prefix}{invite_info.email}"
        # 将邀请信息序列化为JSON格式存储,设置过期时间（从settings中获取）
        await self.set(key, invite_info.model_dump_json(), ex=settings.INVITE_CODE_EXPIRE)

    # 获取邀请信息缓存，根据邮箱查询
    async def get_invite_info(self, email: str) -> InviteInfoSchema | None:
        # 根据邮箱构建缓存键
        key = f"{self.invite_prefix}{email}"
        # 获取缓存的JSON数据
        invite_info_json = await self.get(key)
        # 反序列化为InviteInfoSchema对象
        if invite_info_json is not None:
            invite_info = InviteInfoSchema.model_validate_json(invite_info_json)
            return invite_info
        return None

    # 定义钉钉相关的缓存键前缀
    async def set_dingtalk_info(self, dingtalk_info: DingTalkTokenInfoSchema):
        key = f"{self.dingtalk_prefix}{dingtalk_info.user_id}"
        await self.set(key, dingtalk_info.model_dump_json(), ex=60 * 60 * 24 * 29)

    # 获取钉钉信息缓存，根据用户ID查询
    async def get_dingtalk_info(self, user_id: str):
        key = f"{self.dingtalk_prefix}{user_id}"
        value = await self.get(key)
        return DingTalkTokenInfoSchema.model_validate_json(value)

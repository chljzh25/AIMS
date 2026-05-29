from pydantic_settings import BaseSettings
from pydantic import computed_field, Field
import os
from datetime import timedelta

# 这是一个Pydantic配置类，用于管理HR系统的数据库连接配置。

# 计算项目根目录路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# BaseSettings	Pydantic配置基类，支持从环境变量、.env文件自动加载配置
# Settings 类
# 继承BaseSettings：自动支持从环境变量和.env文件读取配置
# 类型注解：提供类型检查和IDE提示
# 默认值：开发环境的默认配置
class Settings(BaseSettings):
    # DB
    DB_USERNAME: str = "postgres"
    DB_PASSWORD: str = "chljzh"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_NAME: str = "hr_system"

    # JWT配置
    JWT_SECRET_KEY: str = "sfsdfsadfsdfjgafsd"
    # access_token：一般是2个小时过期
    # refresh_token：30天过期
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(days=365)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=365)

    # redis配置
    REDIS_HOST: str = Field('127.0.0.1', validation_alias="REDIS_HOST")
    REDIS_PORT: int = Field(6389, validation_alias="REDIS_PORT")

    # 邀请码过期时间
    INVITE_CODE_EXPIRE: int = 60 * 60 * 24 * 2

    # 邮箱相关的配置
    MAIL_USERNAME: str = Field(..., validation_alias="MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(..., validation_alias="MAIL_PASSWORD")
    MAIL_FROM: str = Field(..., validation_alias="MAIL_USERNAME")
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.qq.com"
    MAIL_FROM_NAME: str = "chljzh"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # 邮箱机器人配置
    EMAIL_BOT_IMAP_HOST: str = "imap.qq.com"
    EMAIL_BOT_SMTP_HOST: str = "smtp.qq.com"
    EMAIL_BOT_EMAIL: str = Field(..., validation_alias="MAIL_USERNAME")
    EMAIL_BOT_PASSWORD: str = Field(..., validation_alias="MAIL_PASSWORD")

    @computed_field  # @computed_field - Pydantic 专用装饰器
    # 作用：这是 Pydantic v2+ 引入的装饰器，用于在 Pydantic 模型中定义计算字段。
    # 专门为 Pydantic 模型设计
    # 会将计算字段纳入 Pydantic 的验证和序列化体系
    # 生成的字段可以被 model_dump()、model_json_schema() 等方法识别
    @property  # Python 内置属性装饰器
    # 作用：将一个方法转换为只读属性，使得调用时不需要加括号 ()，像访问普通属性一样访问方法。
    # 使用场景：当你需要计算一个值，但希望它看起来像一个属性时使用。
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


# 创建全局配置实例
# settings.DATABASE_URL 比 settings.get_database_url() 更直观
settings = Settings()

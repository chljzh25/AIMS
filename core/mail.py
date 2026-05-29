from fastapi_mail import FastMail, ConnectionConfig
from settings import settings


# 创建邮件实例
def create_mail_instance() -> FastMail:
    """创建 FastMail 实例（每次调用返回新实例，线程/协程安全）"""
    # 邮件服务器连接配置类
    mail_config = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=settings.MAIL_STARTTLS,
        MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )
    # 返回一个FastMail对象
    return FastMail(mail_config)

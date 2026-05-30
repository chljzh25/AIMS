import os.path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from dependencies import get_session_instance, get_current_user
from models import AsyncSession
from models.user import UserModel
from settings import settings
from uuid import uuid4
import aiofiles
from core.pdf import WordToPdfConverter
from loguru import logger
from repository.candidate_repo import ResumeRepo
from pathlib import Path
from schemas.candidate_schema import ResumeUploadRespSchema

router = APIRouter(prefix="/candidate", tags=["candidate"])


# 上传简历
@router.post("/resume/upload", summary="上传简历", response_model=ResumeUploadRespSchema)
async def resume_upload(
        file: UploadFile = File(...),
        session: AsyncSession = Depends(get_session_instance),
        current_user: UserModel = Depends(get_current_user),
):
    # 1. 校验文件类型
    # 简历：图片、pdf、word
    allowed_mime_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
        "image/jpg",
    ]
    if file.content_type not in allowed_mime_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该文件不支持！")

    # 2. 保存文件
    resume_dir = settings.RESUME_DIR  # 从设置中获取简历存储目录
    file_extension = os.path.splitext(file.filename)[-1]  # 提取文件扩展名
    unique_filename = f"{uuid4()}{file_extension}"  # 使用UUID生成唯一文件名，避免文件名冲突
    file_path = os.path.join(resume_dir, unique_filename)  # 构建完整文件路径
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
    # 使用异步文件操作保存上传的文件
    try:
        async with aiofiles.open(file_path, mode="wb") as fp:  # 以二进制写模式打开文件
            content = await file.read(1024)  # 每次读取1024字节
            while content:  # 循环直到文件读完
                await fp.write(content)  # 写入文件内容
                content = await file.read(1024)  # 继续读取下一块内容
    finally:
        await fp.close()  # 确保文件被正确关闭

    # 3. 如果是word文档，那么就转化成pdf
    if file_extension == ".doc" or file_extension == ".docx":  # 检查是否为Word文档
        pdf_path = file_path.replace(file_extension, ".pdf")  # 生成对应的PDF文件路径
        converter = WordToPdfConverter(  # 创建Word到PDF转换器实例
            word_path=file_path,  # Word文档路径
            output_pdf_path=pdf_path,  # 输出PDF路径
        )
        try:
            await converter.convert()  # 执行转换操作
            file_path = pdf_path  # 更新文件路径为转换后的PDF文件
        except Exception as e:
            logger.error(f"Word转PDF失败：{e}")  # 记录转换失败的错误日志

    # 4. 将简历数据存储到数据库中
    async with session.begin():
        resume_repo = ResumeRepo(session=session)  # 创建简历仓库实例
        file_name = Path(file_path).name  # 仅获取文件名（不含路径）
        # 创建简历记录，保存文件路径和上传者ID
        resume = await resume_repo.create_resume(file_path=file_name, uploader_id=current_user.id)
    return {"resume": resume}  # 返回包含简历信息的响应

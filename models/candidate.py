import enum
from typing import Optional

from typing import TYPE_CHECKING

# 仅在类型检查时导入
if TYPE_CHECKING:
    from .positions import PositionModel

from sqlalchemy import (
    String, Text, Integer, Enum as SQLAlchemyEnum, ForeignKey, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import BaseModel
from .user import UserModel


# 这是 HR 系统的候选人管理核心模块，包含候选人信息、AI智能筛选评分和简历管理三大功能

# 候选人状态枚举
class CandidateStatusEnum(str, enum.Enum):
    # 1. 已投递
    APPLICATION = "已投递"
    # 2. AI筛选失败
    AI_FILTER_FAILED = "AI筛选失败"
    # 3. AI筛选成功
    AI_FILTER_PASSED = "AI筛选成功"
    # 4. 待面试
    WAITING_FOR_INTERVIEW = "待面试"
    # 5. 拒绝面试
    REFUSED_INTERVIEW = "拒绝面试"
    # 6. 面试通过
    INTERVIEW_PASSED = "面试通过"
    # 7. 面试未通过
    INTERVIEW_REJECTED = "面试未通过"
    # 8. 成功入职
    HIRED = "已入职"
    # 9. HR拒绝候选人
    REJECTED = "已拒绝"


# 性别枚举
class GenderEnum(str, enum.Enum):
    # 1. 男
    MALE = "男"
    # 2. 女
    FEMALE = "女"
    # 3. 其他
    UNKNOWN = "未知"


# CandidateModel 候选人模型
class CandidateModel(BaseModel):
    __tablename__ = "candidates"
    # 核心字段说明
    """
    字段	                类型	                说明
    name	                str	                    候选人姓名
    gender	                GenderEnum	            性别
    birthday	            Optional[str]	        出生日期
    email	                str	                    邮箱地址
    phone_number	        Optional[str]	        手机号码
    work_experience	        Optional[str]	        工作经历
    project_experience	    Optional[str]	        项目经验
    education_experience	Optional[str]	        教育背景
    self_evaluation	        Optional[str]	        自我评价
    other_information	    Optional[str]	        其他信息
    skills	                Optional[str]	        技能特长
    status	                CandidateStatusEnum	    当前状态
    """
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[GenderEnum] = mapped_column(SQLAlchemyEnum(GenderEnum), default=GenderEnum.UNKNOWN, nullable=False)
    birthday: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    work_experience: Mapped[Optional[str]] = mapped_column(Text)
    project_experience: Mapped[Optional[str]] = mapped_column(Text)
    education_experience: Mapped[Optional[str]] = mapped_column(Text)
    self_evaluation: Mapped[Optional[str]] = mapped_column(Text)
    other_information: Mapped[Optional[str]] = mapped_column(Text)
    skills: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[CandidateStatusEnum] = mapped_column(
        SQLAlchemyEnum(CandidateStatusEnum, values_callable=lambda obj: [e.value for e in obj]),
        default=CandidateStatusEnum.APPLICATION, nullable=False
    )

    # 外键字段
    """
    字段	        关联表	    说明
    position_id	    positions	申请的职位
    resume_id	    resumes	    上传的简历
    creator_id	    users	    创建记录的用户
    """
    position_id: Mapped[str] = mapped_column(ForeignKey("positions.id"))
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id"))
    # 这条数据是由谁创建的
    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    # 关系定义
    position: Mapped["PositionModel"] = relationship(back_populates="candidates", lazy="joined")
    resume: Mapped["ResumeModel"] = relationship(back_populates="candidate", uselist=False, lazy="joined")
    creator: Mapped["UserModel"] = relationship(lazy="joined")
    ai_score: Mapped["CandidateAIScoreModel"] = relationship(back_populates="candidate", uselist=False)


# CandidateAIScoreModel AI评分模型
# 这是 HR 系统的智能筛选核心，通过 AI 自动评估候选人匹配度。
class CandidateAIScoreModel(BaseModel):
    __tablename__ = "candidate_ai_scores"
    # 评分字段
    """
    字段	                        类型	    说明
    work_experience_score	        int	        工作经验评分
    technical_skills_score	        int	        技术技能评分
    soft_skills_score	            int	        软技能评分
    educational_background_score	int	        学历背景评分
    project_experience_score	    int	        项目经验评分
    overall_score	                int	        综合评分
    summary	                        str	        AI评估总结
    strengths	                    list[str]	优势分析
    weaknesses	                    list[str]	劣势分析
    """
    work_experience_score: Mapped[int] = mapped_column(Integer, nullable=False)
    technical_skills_score: Mapped[int] = mapped_column(Integer, nullable=False)
    soft_skills_score: Mapped[int] = mapped_column(Integer, nullable=False)
    educational_background_score: Mapped[int] = mapped_column(Integer, nullable=False)
    project_experience_score: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    # 数据存储 使用 JSON 类型存储列表数据，便于灵活扩展。
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"))
    candidate: Mapped["CandidateModel"] = relationship(back_populates="ai_score")


# ResumeModel 简历模型
class ResumeModel(BaseModel):
    __tablename__ = "resumes"
    # file_path：存储简历文件的服务器路径（而非二进制内容）
    # uploader_id：记录谁上传了这份简历
    # 与 CandidateModel 是 1:1 关系
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    uploader_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    uploader: Mapped["UserModel"] = relationship()
    candidate: Mapped["CandidateModel"] = relationship(back_populates="resume")

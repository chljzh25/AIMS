import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import BaseModel
from .user import UserModel
from .candidate import CandidateModel


# 这是 HR 系统的面试安排与结果管理模块，负责记录面试时间、面试官和面试结果

# 面试结果枚举
# 设计意图：标准化面试结果状态，确保数据一致性。
class InterviewResultEnum(str, enum.Enum):
    PENDING = "PENDING"  # 待面试
    PASSED = "PASSED"  # 通过
    FAILED = "FAILED"  # 未通过


# InterviewModel 面试模型
class InterviewModel(BaseModel):
    __tablename__ = "interviews"
    # 字段说明
    """
    字段	            类型	                        说明
    scheduled_time	    Optional[datetime]	            安排的面试时间
    feedback	        Optional[str]	                面试反馈意见
    result	            Optional[InterviewResultEnum]	面试结果
    candidate_id	    str	                            候选人ID（唯一约束）
    interviewer_id	    str	                            面试官ID
    """
    scheduled_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    result: Mapped[Optional[InterviewResultEnum]] = mapped_column(Enum(InterviewResultEnum))

    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), unique=True)
    interviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    # 关系定义
    """
    关系	        说明
    candidate	    关联候选人（反向引用 interviews）
    interviewer	    关联面试官
    """
    candidate: Mapped["CandidateModel"] = relationship(back_populates="interviews")
    interviewer: Mapped["UserModel"] = relationship()


# 动态关系绑定
"""
为什么这样设计？
这是解决循环导入问题的常用技巧：
InterviewModel 需要引用 CandidateModel
CandidateModel 也需要引用 InterviewModel
在文件末尾动态添加关系，避免导入顺序问题
"""
CandidateModel.interviews = relationship("InterviewModel", back_populates="candidate")

import enum
from typing import List, Optional

from typing import TYPE_CHECKING

# 仅在类型检查时导入，避免运行时循环导入
if TYPE_CHECKING:
    from .candidate import CandidateModel

# SQLAlchemyEnum：用于在数据库中存储枚举类型
from sqlalchemy import (
    String, Text, Integer,
    DateTime, Boolean, Enum as SQLAlchemyEnum, ForeignKey
)
# relationship：定义模型之间的关联关系
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import BaseModel
from .user import UserModel, DepartmentModel
from datetime import datetime


# 学历枚举
# 设计意图：标准化学历选项，避免自由文本输入导致的数据不一致。
class EducationEnum(str, enum.Enum):
    # 1. 大专
    COLLEGE = "大专"
    # 2. 本科
    BACHELOR = "本科"
    # 3. 硕士
    MASTER = "硕士"
    # 4. 博士
    DOCTOR = "博士"
    # 5. 未填写
    UNKNOWN = "未知"


class PositionModel(BaseModel):
    __tablename__ = "positions"
    """
    PositionModel 核心字段
    字段	            类型	                约束	        说明
    title	            str	                    非空，100字符	职位名称
    description	        Optional[str]	        Text类型	    职位描述
    requirements	    Optional[str]	        Text类型	    任职要求
    min_salary	        Optional[int]	        -	            最低薪资
    max_salary	        Optional[int]	        -	            最高薪资
    deadline	        Optional[datetime]	    -	            招聘截止日期
    recruitment_count	int	                    默认1            招聘人数
    education	        EducationEnum	        默认UNKNOWN	    最低学历要求
    work_year	        int	                    默认0	        最低工作年限
    is_open	            bool	                默认True	    是否开放招聘
    department_id	    str	                    外键	        所属部门ID
    creator_id	        str	                    外键	        创建者ID
    """
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    requirements: Mapped[Optional[str]] = mapped_column(Text)
    min_salary: Mapped[Optional[int]] = mapped_column(Integer)
    max_salary: Mapped[Optional[int]] = mapped_column(Integer)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime)
    recruitment_count: Mapped[int] = mapped_column(Integer, default=1)
    # 最低学历要求
    education: Mapped[EducationEnum] = mapped_column(SQLAlchemyEnum(EducationEnum), default=EducationEnum.UNKNOWN,
                                                     nullable=False)
    # 最低工作年限要求
    work_year: Mapped[int] = mapped_column(Integer, default=0)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.id"))
    creator_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    # 关系定义
    """
    关系说明：
    关系	        类型	说明
    department	    N:1	    职位所属部门
    creator	        N:1	    职位创建者（HR或管理员）
    candidates	    1:N	    申请该职位的候选人列表
    """
    # relationship(lazy="joined"),使用 joined 加载策略，避免 N+1 查询问题,一次性获取职位、部门和创建者信息
    department: Mapped["DepartmentModel"] = relationship(lazy="joined")
    creator: Mapped["UserModel"] = relationship(lazy="joined")
    candidates: Mapped[List["CandidateModel"]] = relationship(back_populates="position")

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.message import Message
from typing import Optional


# 一个不可变的(frozen)数据类，表示邮件地址：
@dataclass(frozen=True)
class EmailAddress:
    name: str
    address: str


# 一个不可变的(frozen)数据类，表示解析后的邮件：
@dataclass(frozen=True)
class ParsedEmail:
    """A parsed email with convenient fields."""

    uid: str
    message_id: str
    subject: str
    from_: EmailAddress
    to: list[EmailAddress]
    cc: list[EmailAddress]
    date: Optional[datetime]

    text: str
    html: str

    raw: Message

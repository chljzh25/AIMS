from pydantic import BaseModel, EmailStr


class InviteInfoSchema(BaseModel):
    email: EmailStr
    department_id: str
    invite_code: str

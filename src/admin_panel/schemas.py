from pydantic import BaseModel, EmailStr


class admin_request_schema(BaseModel):
    email: EmailStr

from pydantic import BaseModel, EmailStr


class admin_request_schema(BaseModel):
    id: int
    name: str
    surname: str
    email: EmailStr

from pydantic import BaseModel


class ChangeDoc(BaseModel):
    current_name: str
    new_name: str
    description: str

from pydantic import BaseModel


class Feedback(BaseModel):
    value: str
    llm_response: str
    user_comment: str
    request_id: int

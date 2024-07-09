from pydantic import BaseModel


class Feedback(BaseModel):
    value: str
    user_comment: str
    request_id: int

class CheckTest(BaseModel):
    request_id: int
    selected_option: str

class ContestResponse(BaseModel):
    place: int
    name: str
    surname: str
    points: int | float
    total_tests: int

    class Config:
        from_attributes = True

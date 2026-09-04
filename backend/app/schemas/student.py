from pydantic import BaseModel

class StudentCreate(BaseModel):
    student_id: str
    name: str
    age: int
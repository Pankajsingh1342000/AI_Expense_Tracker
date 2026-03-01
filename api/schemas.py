from pydantic import BaseModel

class AskRequest(BaseModel):
    command: str

class AskResponse(BaseModel):
    result: dict
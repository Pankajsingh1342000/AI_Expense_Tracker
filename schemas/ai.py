from pydantic import BaseModel

class AIQuery(BaseModel):
    query: str
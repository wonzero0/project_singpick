from pydantic import BaseModel

class RequestReserve(BaseModel):
    booth_id: int
    song_id: int
    user_id: str
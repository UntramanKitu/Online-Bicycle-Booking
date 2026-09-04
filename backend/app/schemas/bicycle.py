from pydantic import BaseModel


class BicycleResponse(BaseModel):
    id: int
    code: str
    type: str
    model: str
    station: str
    distance: str
    tint: str
    battery: int | None = None
    available: bool

from pydantic import BaseModel
from typing import List, Optional

class LocationRequest(BaseModel):
    lat: float
    lng: float
    radius_m: Optional[int] = 5000
    indoor: Optional[bool] = False

class RouteRequest(BaseModel):
    waypoints: List[List[float]]  # [[lat, lng], [lat, lng], ...]
    indoor: Optional[bool] = False

class CoverageGapRequest(BaseModel):
    state: Optional[str] = None  # if None, returns all states

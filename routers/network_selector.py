from fastapi import APIRouter, HTTPException
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import LocationRequest
from signal_engine import get_best_network

router = APIRouter()

@router.post("/best-network")
def best_network(req: LocationRequest):
    # Validate India coordinates
    if not (6.0 <= req.lat <= 37.0 and 68.0 <= req.lng <= 98.0):
        raise HTTPException(status_code=400, detail="Coordinates outside India bounds")

    result = get_best_network(
        lat=req.lat,
        lng=req.lng,
        radius_m=req.radius_m,
        indoor=req.indoor
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result

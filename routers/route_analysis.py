from fastapi import APIRouter, HTTPException
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import RouteRequest
from signal_engine import get_best_network

router = APIRouter()

@router.post("/route-analysis")
def route_analysis(req: RouteRequest):
    if len(req.waypoints) < 2:
        raise HTTPException(status_code=400, detail="Minimum 2 waypoints required")

    if len(req.waypoints) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 waypoints allowed")

    segment_results = []
    operator_wins   = {}

    for i, point in enumerate(req.waypoints):
        lat, lng = point[0], point[1]

        result = get_best_network(lat=lat, lng=lng, indoor=req.indoor)

        if "error" not in result and result['ranked_operators']:
            best = result['ranked_operators'][0]
            segment_results.append({
                "waypoint":    i + 1,
                "lat":         lat,
                "lng":         lng,
                "best_operator": best['operator'],
                "signal_dbm":  best['signal_dbm'],
                "quality":     best['quality'],
                "radio_type":  best['radio_type']
            })
            op = best['operator']
            operator_wins[op] = operator_wins.get(op, 0) + 1
        else:
            segment_results.append({
                "waypoint": i + 1,
                "lat": lat,
                "lng": lng,
                "best_operator": "No coverage",
                "signal_dbm": None,
                "quality": "No Signal",
                "radio_type": None
            })

    overall_winner = max(operator_wins, key=operator_wins.get) if operator_wins else "No coverage"

    return {
        "total_waypoints":  len(req.waypoints),
        "overall_winner":   overall_winner,
        "operator_wins":    operator_wins,
        "segments":         segment_results
    }

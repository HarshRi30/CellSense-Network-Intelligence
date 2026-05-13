from fastapi import APIRouter
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_conn, get_cursor

router = APIRouter()

@router.get("/coverage-gap")
def coverage_gap(state: str = None):
    conn = get_conn()
    cur  = get_cursor(conn)

    if state:
        cur.execute("""
            SELECT 
                t.state_circle,
                t.operator,
                COUNT(*) AS tower_count,
                ROUND(COUNT(*)::decimal / MAX(d.area_sqkm), 4) AS towers_per_sqkm,
                ROUND(MAX(d.area_sqkm) / NULLIF(COUNT(*), 0), 2) AS sqkm_per_tower
            FROM towers t
            JOIN districts d ON t.state_circle = d.district_name
            WHERE t.operator = ANY(ARRAY['Jio','Airtel','Vi','BSNL'])
            AND t.state_circle ILIKE %s
            GROUP BY t.state_circle, t.operator
            ORDER BY tower_count DESC
        """, (f"%{state}%",))
    else:
        cur.execute("""
            SELECT 
                t.state_circle,
                COUNT(*) AS total_towers,
                COUNT(*) FILTER (WHERE t.operator = 'Jio')    AS jio_towers,
                COUNT(*) FILTER (WHERE t.operator = 'Airtel') AS airtel_towers,
                COUNT(*) FILTER (WHERE t.operator = 'Vi')     AS vi_towers,
                COUNT(*) FILTER (WHERE t.operator = 'BSNL')   AS bsnl_towers,
                ROUND(COUNT(*)::decimal / MAX(d.area_sqkm), 4) AS towers_per_sqkm,
                ROUND(MAX(d.area_sqkm) / NULLIF(COUNT(*), 0), 2) AS sqkm_per_tower,
                MAX(d.towers_5g) AS towers_5g,
                RANK() OVER (ORDER BY COUNT(*)::decimal / MAX(d.area_sqkm) ASC) AS gap_rank
            FROM towers t
            JOIN districts d ON t.state_circle = d.district_name
            WHERE t.operator = ANY(ARRAY['Jio','Airtel','Vi','BSNL'])
            AND t.state_circle IS NOT NULL
            GROUP BY t.state_circle
            ORDER BY towers_per_sqkm ASC
        """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [dict(row) for row in rows]

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import network_selector, coverage_gap, route_analysis

app = FastAPI(
    title="CellSense API",
    description="India Network Coverage Intelligence Platform",
    version="1.0.0"
)

# CORS — allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(network_selector.router, prefix="/api", tags=["Network Selector"])
app.include_router(coverage_gap.router,     prefix="/api", tags=["Coverage Gap"])
app.include_router(route_analysis.router,   prefix="/api", tags=["Route Analysis"])

@app.get("/")
def root():
    return {
        "project": "CellSense",
        "version": "1.0.0",
        "status":  "running",
        "docs":    "/docs"
    }

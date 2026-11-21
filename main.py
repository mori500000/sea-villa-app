from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Sea Villa Climate Simulator API")

class SimulationRequest(BaseModel):
    location_id: str
    year: int
    temperature_anomaly: float  # 例: 1.5 (°C 上昇)

@app.post("/simulate")
def simulate_ecosystem(req: SimulationRequest):
    # 簡易的なシミュレーションロジック
    bleaching_rate = min(100.0, max(0.0, req.temperature_anomaly * 40.0))
    turtle_presence = max(0.0, 1.0 - (req.temperature_anomaly * 0.3))
    
    status = "healthy"
    if bleaching_rate > 70:
        status = "severely_bleached (ruins)"
    elif bleaching_rate > 30:
        status = "partially_bleached"

    return {
        "location_id": req.location_id,
        "year": req.year,
        "temperature_anomaly": req.temperature_anomaly,
        "coral_health": {
            "bleaching_rate_percent": bleaching_rate,
            "status": status
        },
        "sea_turtle": {
            "presence_probability": turtle_presence
        }
    }

from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Hotel Rate Calculation Service")

class CalculationRequest(BaseModel):
    check_in: date
    check_out: date
    base_price_per_night: float

@app.post("/calculate")
def calculate_cost(req: CalculationRequest):
    if req.check_out <= req.check_in:
        raise HTTPException(status_code=400, detail="Дата выезда должна быть позже даты заезда")
    
    nights = (req.check_out - req.check_in).days
    total = round(nights * req.base_price_per_night, 2)
    
    return {
        "nights": nights,
        "rate_per_night": req.base_price_per_night,
        "total_price": total
    }

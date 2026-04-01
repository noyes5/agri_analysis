from pydantic import BaseModel
from typing import Optional

class WeatherHistoryCreate(BaseModel):
    date: str
    avg_ta: float
    max_ta: float
    min_ta: float
    sum_rn: float

class PriceCreate(BaseModel):
    date: str
    item_name: str
    kind_name: str
    item_code: Optional[str] = "" 
    location: Optional[str] = ""
    unit: Optional[str] = ""
    price: float

    class Config:
        from_attributes = True

class WeatherForecastCreate(BaseModel):
    date: str
    fcst_time: str
    category: str
    fcst_value: float
    reg_date: str

    class Config:
        from_attributes = True
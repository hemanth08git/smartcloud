from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ==========================
# Product models
# ==========================

class ProductBase(BaseModel):
    name: str = Field(..., example="Yoghurt")
    category: Optional[str] = Field(None, example="Dairy")
    description: Optional[str] = Field(None, example="Natural yoghurt 500ml")


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class Product(ProductBase):
    id: int

    class Config:
        orm_mode = True


# ==========================
# Batch models
# ==========================

class BatchBase(BaseModel):
    product_id: int
    code: str = Field(..., example="BATCH-2025-001")
    status: Optional[str] = Field("IN_PROGRESS")
    line_id: Optional[str] = Field(None, example="LINE-1")


class BatchCreate(BatchBase):
    pass


class BatchUpdate(BaseModel):
    status: Optional[str] = None
    line_id: Optional[str] = None


class Batch(BatchBase):
    id: int
    started_at: datetime
    ended_at: Optional[datetime]
    risk_level: str
    risk_score: Optional[float]
    risk_explanation: Optional[str]

    class Config:
        orm_mode = True


# ==========================
# Inspection models
# ==========================

class InspectionBase(BaseModel):
    batch_id: int
    temperature: float
    humidity: Optional[float] = None
    ph: Optional[float] = None
    microbial_result: Optional[str] = "PENDING"
    notes: Optional[str] = None


class InspectionCreate(InspectionBase):
    pass


class Inspection(InspectionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ==========================
# Sensor reading models
# ==========================

class SensorReadingBase(BaseModel):
    batch_id: int
    temperature: float
    humidity: Optional[float] = None


class SensorReadingCreate(SensorReadingBase):
    pass


class SensorReading(SensorReadingBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ==========================
# Alert models
# ==========================

class Alert(BaseModel):
    id: int
    batch_id: int
    level: str
    message: str
    created_at: datetime

    class Config:
        orm_mode = True


# ==========================
# Dashboard summary
# ==========================

class DashboardSummary(BaseModel):
    total_products: int
    total_batches: int
    high_risk_batches: int
    medium_risk_batches: int
    low_risk_batches: int
    unknown_risk_batches: int


# ==========================
# Generic anomaly request/response (history + current)
# ==========================

class SensorSample(BaseModel):
    temperature: float
    humidity: float


class AnomalyRequest(BaseModel):
    history: List[SensorSample]   # past readings
    current: SensorSample         # new reading to evaluate


class AnomalyResponse(BaseModel):
    is_anomaly: bool
    score: float
    level: str
    message: str


# ==========================
# Batch anomaly (DB-based PyOD) models
# ==========================

class CurrentSensorReading(BaseModel):
    temperature: float
    humidity: float


class BatchAnomalyResponse(BaseModel):
    batch_id: int
    is_anomaly: bool
    score: float
    level: str
    message: str

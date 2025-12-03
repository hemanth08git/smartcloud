# app/main.py

from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import schemas, db_dynamo
from . import models, crud
from .database import engine, Base
from .deps import get_db

from food_quality_analyzer.models import (
    EnvironmentProfile,
    SpoilageRiskModel,
    SensorSample,
)
from food_quality_analyzer.anomaly import SensorAnomalyDetector


# -------------------------------------------------------------------
# DB init (SQLAlchemy: batches, inspections, sensor readings, alerts)
# -------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Food Production & Quality Monitoring API")

# -------------------------------------------------------------------
# CORS so the frontend (different origin) can call the backend
# -------------------------------------------------------------------
origins = [
    # local dev
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://localhost:5173",
    # S3 static website (update if your bucket/URL changes)
    "http://smartfood-frontend-x25104683.s3-website-us-east-1.amazonaws.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================
# Health
# ==========================
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


# ==========================
# Products  (in-memory store via db_dynamo)
# ==========================
# NOTE: data is kept only in RAM and resets when the server restarts.


@app.get("/products", response_model=List[schemas.Product], tags=["products"])
def list_products():
    return db_dynamo.list_products()


@app.post("/products", response_model=schemas.Product, tags=["products"])
def create_product(product_in: schemas.ProductCreate):
    return db_dynamo.create_product(product_in)


@app.put("/products/{product_id}", response_model=schemas.Product, tags=["products"])
def update_product(
    product_id: int,
    product_in: schemas.ProductUpdate,
):
    product = db_dynamo.update_product(product_id, product_in)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.delete("/products/{product_id}", tags=["products"])
def delete_product(product_id: int):
    ok = db_dynamo.delete_product(product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"ok": True}


# ==========================
# Batches  (SQLAlchemy)
# ==========================
@app.get("/batches", response_model=List[schemas.Batch], tags=["batches"])
def list_batches(db: Session = Depends(get_db)):
    return crud.get_batches(db)


@app.post("/batches", response_model=schemas.Batch, tags=["batches"])
def create_batch(batch_in: schemas.BatchCreate, db: Session = Depends(get_db)):
    return crud.create_batch(db, batch_in)


@app.put("/batches/{batch_id}", response_model=schemas.Batch, tags=["batches"])
def update_batch(
    batch_id: int,
    batch_in: schemas.BatchUpdate,
    db: Session = Depends(get_db),
):
    batch = crud.update_batch(db, batch_id, batch_in)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@app.delete("/batches/{batch_id}", tags=["batches"])
def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_batch(db, batch_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Batch not found")
    return {"ok": True}


# ==========================
# Inspections
# ==========================
@app.get(
    "/batches/{batch_id}/inspections",
    response_model=List[schemas.Inspection],
    tags=["inspections"],
)
def list_inspections(batch_id: int, db: Session = Depends(get_db)):
    return crud.get_inspections_for_batch(db, batch_id)


@app.post("/inspections", response_model=schemas.Inspection, tags=["inspections"])
def create_inspection(
    inspection_in: schemas.InspectionCreate,
    db: Session = Depends(get_db),
):
    # Ensure batch exists
    batch = db.query(models.Batch).filter(models.Batch.id == inspection_in.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return crud.create_inspection(db, inspection_in)


# ==========================
# Sensor readings & risk scoring
# ==========================
@app.post(
    "/sensor-readings",
    response_model=schemas.SensorReading,
    tags=["sensor"],
)
def create_sensor_reading(
    reading_in: schemas.SensorReadingCreate,
    db: Session = Depends(get_db),
):
    batch = db.query(models.Batch).filter(models.Batch.id == reading_in.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return crud.create_sensor_reading(db, reading_in)


@app.post(
    "/batches/{batch_id}/compute-risk",
    response_model=schemas.Batch,
    tags=["risk"],
)
def compute_risk(batch_id: int, db: Session = Depends(get_db)):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    readings = crud.get_sensor_readings_for_batch(db, batch_id)
    samples = [
        SensorSample(temperature=r.temperature, humidity=r.humidity)
        for r in readings
    ]

    profile = EnvironmentProfile.from_samples(samples)
    model = SpoilageRiskModel()
    result = model.evaluate(profile)

    batch.risk_level = result.level
    batch.risk_score = result.score
    batch.risk_explanation = result.explanation

    # Create alert if medium or high
    if result.level in ("MEDIUM", "HIGH"):
        crud.create_alert(
            db,
            batch_id=batch.id,
            level=result.level,
            message=f"Batch {batch.code} has {result.level} spoilage risk. {result.explanation}",
        )

    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


# ==========================
# Alerts & dashboard
# ==========================
@app.get("/alerts", response_model=List[schemas.Alert], tags=["alerts"])
def list_alerts(db: Session = Depends(get_db)):
    return crud.get_recent_alerts(db)


@app.get(
    "/dashboard/summary",
    response_model=schemas.DashboardSummary,
    tags=["dashboard"],
)
def dashboard_summary(db: Session = Depends(get_db)):
    return crud.get_dashboard_summary(db)


# ==========================
# PyOD anomaly detection (batch-based)
# ==========================
@app.post(
    "/sensor/analyze/batch/{batch_id}",
    response_model=schemas.BatchAnomalyResponse,
    tags=["anomaly"],
)
def analyze_batch_sensor_reading(
    batch_id: int,
    payload: schemas.CurrentSensorReading,
    db: Session = Depends(get_db),
):
    """
    Use PyOD (Isolation Forest) to detect if the current sensor reading
    for this batch is anomalous compared to its recent history in DB.
    """
    # 1. Load history from DB
    history_rows = crud.get_recent_sensor_readings(db, batch_id=batch_id, limit=50)

    if not history_rows:
        raise HTTPException(
            status_code=404,
            detail=f"No sensor history found for batch {batch_id}.",
        )

    history = [
        {
            "temperature": float(r.temperature),
            "humidity": float(r.humidity),
        }
        for r in history_rows
    ]

    # 2. Prepare detector
    detector = SensorAnomalyDetector()
    detector.fit(history)

    current_dict = {
        "temperature": float(payload.temperature),
        "humidity": float(payload.humidity),
    }

    # 3. Predict anomaly
    result = detector.predict_one(current_dict)

    return schemas.BatchAnomalyResponse(
        batch_id=batch_id,
        is_anomaly=result["is_anomaly"],
        score=result["score"],
        level=result["level"],
        message=result["message"],
    )

from typing import List, Optional

from sqlalchemy.orm import Session

from . import models, schemas, db_dynamo


# ==========================
# Product CRUD (SQL)
# NOTE: Currently your FastAPI /products endpoints use db_dynamo
# for an in-memory / Dynamo-style store. These helpers operate
# on the relational Product table and are kept for completeness.
# ==========================

def get_products(db: Session) -> List[models.Product]:
    return db.query(models.Product).all()


def create_product(db: Session, product_in: schemas.ProductCreate) -> models.Product:
    product = models.Product(**product_in.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session,
    product_id: int,
    product_in: schemas.ProductUpdate
) -> Optional[models.Product]:
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return None
    for field, value in product_in.dict(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> bool:
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return False
    db.delete(product)
    db.commit()
    return True


# ==========================
# Batch CRUD
# ==========================

def get_batches(db: Session) -> List[models.Batch]:
    return db.query(models.Batch).all()


def create_batch(db: Session, batch_in: schemas.BatchCreate) -> models.Batch:
    batch = models.Batch(**batch_in.dict())
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def update_batch(
    db: Session,
    batch_id: int,
    batch_in: schemas.BatchUpdate
) -> Optional[models.Batch]:
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        return None
    for field, value in batch_in.dict(exclude_unset=True).items():
        setattr(batch, field, value)
    db.commit()
    db.refresh(batch)
    return batch


def delete_batch(db: Session, batch_id: int) -> bool:
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        return False
    db.delete(batch)
    db.commit()
    return True


# ==========================
# Inspections
# ==========================

def get_inspections_for_batch(db: Session, batch_id: int) -> List[models.Inspection]:
    return (
        db.query(models.Inspection)
        .filter(models.Inspection.batch_id == batch_id)
        .all()
    )


def create_inspection(
    db: Session,
    inspection_in: schemas.InspectionCreate
) -> models.Inspection:
    inspection = models.Inspection(**inspection_in.dict())
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection


# ==========================
# Sensor readings
# ==========================

def create_sensor_reading(
    db: Session,
    reading_in: schemas.SensorReadingCreate
) -> models.SensorReading:
    reading = models.SensorReading(**reading_in.dict())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def get_sensor_readings_for_batch(
    db: Session,
    batch_id: int
) -> List[models.SensorReading]:
    return (
        db.query(models.SensorReading)
        .filter(models.SensorReading.batch_id == batch_id)
        .all()
    )


def get_recent_sensor_readings(
    db: Session,
    batch_id: int,
    limit: int = 50
) -> List[models.SensorReading]:
    """
    Return the most recent sensor readings for a given batch.
    Assumes models.SensorReading has fields: batch_id, temperature,
    humidity, timestamp.
    """
    return (
        db.query(models.SensorReading)
        .filter(models.SensorReading.batch_id == batch_id)
        .order_by(models.SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )


# ==========================
# Alerts & dashboard
# ==========================

def create_alert(
    db: Session,
    batch_id: int,
    level: str,
    message: str
) -> models.Alert:
    alert = models.Alert(batch_id=batch_id, level=level, message=message)
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_recent_alerts(db: Session, limit: int = 20) -> List[models.Alert]:
    return (
        db.query(models.Alert)
        .order_by(models.Alert.created_at.desc())
        .limit(limit)
        .all()
    )


def get_dashboard_summary(db: Session) -> schemas.DashboardSummary:
    """
    Dashboard metrics:
    - Product count from the Dynamo-style product store (db_dynamo),
      so it matches what the /products API exposes.
    - Batch & risk stats from the relational database.
    """
    # products are managed through db_dynamo (DynamoDB-style layer)
    total_products = len(db_dynamo.list_products())

    total_batches = db.query(models.Batch).count()
    high_risk = (
        db.query(models.Batch)
        .filter(models.Batch.risk_level == "HIGH")
        .count()
    )
    medium_risk = (
        db.query(models.Batch)
        .filter(models.Batch.risk_level == "MEDIUM")
        .count()
    )
    low_risk = (
        db.query(models.Batch)
        .filter(models.Batch.risk_level == "LOW")
        .count()
    )
    unknown_risk = (
        db.query(models.Batch)
        .filter(models.Batch.risk_level == "UNKNOWN")
        .count()
    )

    return schemas.DashboardSummary(
        total_products=total_products,
        total_batches=total_batches,
        high_risk_batches=high_risk,
        medium_risk_batches=medium_risk,
        low_risk_batches=low_risk,
        unknown_risk_batches=unknown_risk,
    )

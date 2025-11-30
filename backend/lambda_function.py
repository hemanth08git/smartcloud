import json
import os
import uuid
from decimal import Decimal
from datetime import datetime, timezone

import boto3

# === DynamoDB setup ===
dynamodb = boto3.resource("dynamodb")

PRODUCTS_TABLE = os.getenv("PRODUCTS_TABLE", "SmartFoodProducts")
BATCHES_TABLE = os.getenv("BATCHES_TABLE", "SmartFoodBatches")
READINGS_TABLE = os.getenv("READINGS_TABLE", "SmartFoodSensorReadings")
ALERTS_TABLE = os.getenv("ALERTS_TABLE", "SmartFoodAlerts")

products_table = dynamodb.Table(PRODUCTS_TABLE)
batches_table = dynamodb.Table(BATCHES_TABLE)
readings_table = dynamodb.Table(READINGS_TABLE)
alerts_table = dynamodb.Table(ALERTS_TABLE)


# === Helpers ===
def decimal_default(obj):
    """Convert DynamoDB Decimal -> float for JSON responses."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def resp(status_code: int, body):
    """Standard API response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
        },
        "body": json.dumps(body, default=decimal_default),
    }


def parse_body(event):
    body_str = event.get("body") or "{}"
    try:
        return json.loads(body_str)
    except json.JSONDecodeError:
        return {}


# === Products ===
def list_products():
    data = products_table.scan()
    items = data.get("Items", [])
    return resp(200, items)


def create_product(event):
    body = parse_body(event)

    name = body.get("name")
    if not name:
        return resp(400, {"error": "name is required"})

    product_id = body.get("product_id") or f"P-{uuid.uuid4().hex[:8]}"

    item = {
        "product_id": product_id,
        "name": name,
        "category": body.get("category", ""),
        "description": body.get("description", ""),
    }

    products_table.put_item(Item=item)
    return resp(201, item)


# === Batches ===
def list_batches():
    data = batches_table.scan()
    items = data.get("Items", [])
    return resp(200, items)


def create_batch(event):
    body = parse_body(event)

    product_id = body.get("product_id")
    if not product_id:
        return resp(400, {"error": "product_id is required"})

    batch_id = body.get("batch_id") or f"BATCH-{uuid.uuid4().hex[:8]}"
    code = body.get("code", batch_id)

    item = {
        "batch_id": batch_id,
        "product_id": product_id,
        "code": code,
        "status": body.get("status", "IN_PROGRESS"),
        "line_id": body.get("line_id", ""),
        "risk_level": body.get("risk_level", "UNKNOWN"),
        "risk_score": body.get("risk_score", 0.0),
        "risk_explanation": body.get("risk_explanation", ""),
        "started_at": body.get("started_at", now_iso()),
        "ended_at": body.get("ended_at"),  # can be None
    }

    batches_table.put_item(Item=item)
    return resp(201, item)


# === Sensor readings ===
def add_sensor_reading(event):
    body = parse_body(event)

    batch_id = body.get("batch_id")
    if not batch_id:
        return resp(400, {"error": "batch_id is required"})

    try:
        temperature = Decimal(str(body.get("temperature")))
    except Exception:
        return resp(400, {"error": "temperature is required and must be numeric"})

    humidity_val = body.get("humidity")
    humidity = Decimal(str(humidity_val)) if humidity_val is not None else None

    timestamp = body.get("timestamp") or now_iso()

    item = {
        "batch_id": batch_id,
        "timestamp": timestamp,
        "temperature": temperature,
    }
    if humidity is not None:
        item["humidity"] = humidity

    readings_table.put_item(Item=item)
    return resp(201, item)


def list_sensor_readings_for_batch(batch_id: str):
    # Query by batch_id, sorted by timestamp
    data = readings_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("batch_id").eq(batch_id),
        ScanIndexForward=True,  # oldest -> newest
    )
    items = data.get("Items", [])
    return resp(200, items)


# === Alerts & dashboard ===
def list_alerts():
    data = alerts_table.scan()
    items = data.get("Items", [])
    # optionally sort by created_at descending in code
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return resp(200, items[:50])  # latest 50
        

def dashboard_summary():
    """
    Compute summary from SmartFoodBatches:
    total products, total batches, and risk level counts.
    """
    # total products:
    prod_scan = products_table.scan()
    total_products = len(prod_scan.get("Items", []))

    # batches and risk breakdown
    batch_scan = batches_table.scan()
    batches = batch_scan.get("Items", [])

    total_batches = len(batches)
    high = medium = low = unknown = 0

    for b in batches:
        level = (b.get("risk_level") or "UNKNOWN").upper()
        if level == "HIGH":
            high += 1
        elif level == "MEDIUM":
            medium += 1
        elif level == "LOW":
            low += 1
        else:
            unknown += 1

    summary = {
        "total_products": total_products,
        "total_batches": total_batches,
        "high_risk_batches": high,
        "medium_risk_batches": medium,
        "low_risk_batches": low,
        "unknown_risk_batches": unknown,
    }
    return resp(200, summary)


# === Lambda entrypoint / Router ===
def lambda_handler(event, context):
    """
    Single Lambda behind API Gateway HTTP API (proxy).
    Routes by path + method:
      GET  /products
      POST /products
      GET  /batches
      POST /batches
      GET  /batches/{batch_id}/sensor-readings
      POST /sensor-readings
      GET  /alerts
      GET  /dashboard/summary
    """
    # HTTP API (v2) uses requestContext.http.method
    method = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method", event.get("httpMethod", "GET"))
    )
    raw_path = event.get("rawPath") or event.get("path") or "/"

    # CORS preflight
    if method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
            },
            "body": "",
        }

    # Normalise
    path = raw_path.rstrip("/") or "/"

    # ---- Products ----
    if path == "/products":
        if method == "GET":
            return list_products()
        elif method == "POST":
            return create_product(event)

    # ---- Batches ----
    if path == "/batches":
        if method == "GET":
            return list_batches()
        elif method == "POST":
            return create_batch(event)

    # ---- Sensor readings ----
    if path == "/sensor-readings" and method == "POST":
        return add_sensor_reading(event)

    # /batches/{batch_id}/sensor-readings
    parts = path.strip("/").split("/")
    if len(parts) == 3 and parts[0] == "batches" and parts[2] == "sensor-readings":
        batch_id = parts[1]
        if method == "GET":
            return list_sensor_readings_for_batch(batch_id)

    # ---- Alerts ----
    if path == "/alerts" and method == "GET":
        return list_alerts()

    # ---- Dashboard ----
    if path == "/dashboard/summary" and method == "GET":
        return dashboard_summary()

    # Default 404
    return resp(404, {"message": f"No route for {method} {path}"})

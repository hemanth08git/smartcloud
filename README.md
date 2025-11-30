# Smart Food Production & Quality Monitoring System

This is a simple end-to-end demo application for a **Food & Beverage Manufacturing**
cloud project. It includes:

- A **FastAPI** backend with CRUD and non-CRUD operations
- A small **custom analytics library** (`food_quality_analyzer`) for spoilage risk
- A **vanilla HTML/JavaScript frontend** with a "cloud-style" dashboard UI

## 1. Prerequisites

- Python 3.10+ installed
- Node is **not** required (frontend is plain HTML + JS)
- Recommended: create and activate a virtual environment

## 2. Backend Setup (Local)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

By default it will run at: `http://127.0.0.1:8000`

You can open the interactive API docs at: `http://127.0.0.1:8000/docs`.

A SQLite database file `food_quality.db` will be created in the `backend/` folder.

## 3. Frontend Setup (Local)

The frontend is a simple static site.

You can open `frontend/index.html` directly in the browser, or serve it
with a simple static server, e.g.:

```bash
cd frontend
python -m http.server 5500
```

Then visit: `http://127.0.0.1:5500/index.html`

Make sure the backend is running on `http://127.0.0.1:8000`.

## 4. Features

### CRUD Operations

- **Products**
  - List, create, update, delete

- **Batches**
  - List, create, update, delete

- **Inspections**
  - List inspections for a batch
  - Create new inspection entries

- **Sensor Readings**
  - Create readings per batch (temperature, humidity)

### Non-CRUD Operations

- **Compute Risk**  
  For a given batch, compute spoilage risk based on sensor readings using
  the `food_quality_analyzer` library. Risk level is one of:
  - `LOW`
  - `MEDIUM`
  - `HIGH`
  - `UNKNOWN` (no data)

- **Alerts**  
  If a batch risk is MEDIUM or HIGH, an alert is created.

- **Dashboard Summary**  
  Aggregated counts:
  - total products
  - total batches
  - high / medium / low / unknown risk batches

## 5. Frontend UI

The frontend provides:

- A **dashboard** showing key summary metrics
- Tabs for:
  - Products
  - Batches
  - Inspections
  - Alerts

Use the forms to add new products, batches, inspections, and sensor readings.
Then compute risk for a batch and see alerts appear.



from mangum import Mangum
from app.main import app  # your FastAPI app

handler = Mangum(app)

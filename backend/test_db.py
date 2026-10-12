from app.db.session import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"Database connection successful! Result: {result.scalar()}")
except Exception as e:
    print(f"Error connecting to database: {e}")

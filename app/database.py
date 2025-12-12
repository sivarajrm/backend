from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

# Read DB URL (SQLite / PostgreSQL / MySQL etc.)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./health.db")

# SQLite requires special argument
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model
Base = declarative_base()

# ✅ Provide DB session dependency so ALL routes can import get_db()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

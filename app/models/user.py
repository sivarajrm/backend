from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    azure_id = Column(String, unique=True, index=True, nullable=False)  # MSAL ID string
    name = Column(String)
    email = Column(String, unique=True)
    profile_pic = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    records = relationship("HealthRecord", back_populates="user", cascade="all, delete-orphan")
    insights = relationship("HealthInsight", back_populates="user", cascade="all, delete-orphan")

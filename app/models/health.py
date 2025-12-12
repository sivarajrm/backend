from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    # KEY: this must match users.azure_id type and name
    user_id = Column(String, ForeignKey("users.azure_id"), nullable=False)

    gender = Column(String)
    age = Column(Float)
    height = Column(Float)
    weight = Column(Float)
    bloodPressureSys = Column(Float)
    bloodPressureDia = Column(Float)
    heartRate = Column(Float)
    sleepHours = Column(Float)
    waterIntake = Column(Float)
    workoutMinutes = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="records")
    insights = relationship("HealthInsight", back_populates="record", cascade="all, delete-orphan")


class HealthInsight(Base):
    __tablename__ = "health_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.azure_id"), nullable=False)
    health_record_id = Column(Integer, ForeignKey("health_records.id"))

    summary = Column(String)
    risk_level = Column(String)
    diet = Column(String)
    fitness = Column(String)
    goals = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    record = relationship("HealthRecord", back_populates="insights")
    user = relationship("User", back_populates="insights")

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Atharva")
    weight_kg = Column(Float, default=75.0)
    height_cm = Column(Float, default=175.0)
    age = Column(Integer, default=24)

class Workout(Base):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)
    workout_type = Column(String)        # "running", "push day", "cycling"
    duration_minutes = Column(Integer)
    intensity = Column(Integer, default=3)  # 1-5
    calories_burned = Column(Float)
    source = Column(String, default="manual")  # "manual", "alexa", "watch"
    performed_at = Column(DateTime, server_default=func.now())

class Meal(Base):
    __tablename__ = "meals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1)
    meal_type = Column(String)           # "breakfast", "lunch", "dinner", "snack"
    food_name = Column(String)
    calories = Column(Float)
    protein_g = Column(Float, default=0)
    carbs_g = Column(Float, default=0)
    fat_g = Column(Float, default=0)
    source = Column(String, default="manual")  # "manual", "alexa", "watch"
    logged_at = Column(DateTime, server_default=func.now())
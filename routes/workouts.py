from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Workout
from pydantic import BaseModel
from datetime import date

router = APIRouter()

# MET values for calorie calculation
MET_VALUES = {
    "running": 9.0,
    "walking": 3.5,
    "cycling": 7.0,
    "swimming": 8.0,
    "push day": 6.0,
    "pull day": 6.0,
    "leg day": 6.0,
    "hiit": 8.0,
    "yoga": 3.0,
    "default": 5.0
}

class WorkoutIn(BaseModel):
    workout_type: str
    duration_minutes: int
    intensity: int = 3
    source: str = "manual"

@router.post("/workouts")
def log_workout(data: WorkoutIn, db: Session = Depends(get_db)):
    met = MET_VALUES.get(data.workout_type.lower(), MET_VALUES["default"])
    weight_kg = 75.0  # default, later pull from user profile
    calories = met * weight_kg * (data.duration_minutes / 60)

    workout = Workout(
        workout_type=data.workout_type,
        duration_minutes=data.duration_minutes,
        intensity=data.intensity,
        calories_burned=round(calories, 1),
        source=data.source
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return {"message": "Workout logged", "calories_burned": workout.calories_burned, "id": workout.id}

@router.get("/workouts")
def get_workouts(db: Session = Depends(get_db)):
    workouts = db.query(Workout).order_by(Workout.performed_at.desc()).limit(20).all()
    return workouts
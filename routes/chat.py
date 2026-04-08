from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Workout, Meal
from pydantic import BaseModel
from openai import OpenAI
import os

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatIn(BaseModel):
    message: str

@router.post("/chat")
def chat(data: ChatIn, db: Session = Depends(get_db)):
    # Get today's context from DB
    workouts = db.query(Workout).limit(5).all()
    meals = db.query(Meal).limit(5).all()

    context = f"""
    Recent workouts: {[f"{w.workout_type} {w.duration_minutes}min {w.calories_burned}kcal" for w in workouts]}
    Recent meals: {[f"{m.food_name} {m.calories}kcal" for m in meals]}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You are a personal fitness assistant. User data: {context}"},
            {"role": "user", "content": data.message}
        ]
    )
    return {"reply": response.choices[0].message.content}
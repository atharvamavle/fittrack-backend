from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routes import workouts, meals, summary, chat
from routes import workouts, meals, summary, chat, report  # add report



# Create all DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FitTrack API")

# Allow React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workouts.router, prefix="/api")
app.include_router(meals.router, prefix="/api")
app.include_router(summary.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

app.include_router(report.router, prefix="/api") 

@app.get("/")
def root():
    return {"message": "FitTrack API is running"}
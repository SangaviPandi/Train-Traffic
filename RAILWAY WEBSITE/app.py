# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend import router as reschedule_router
from backend_schedule import router as schedule_router

app = FastAPI()

# Enable CORS for local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from both modules
app.include_router(reschedule_router)
app.include_router(schedule_router)
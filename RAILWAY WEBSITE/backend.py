# backend.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Literal
import numpy as np
import joblib

router = APIRouter()

actions = ["Allow", "Hold", "Reroute"]
Q = joblib.load("squee1/q_table_scheduler.joblib")  # Update path separator to slash

class RescheduleRequest(BaseModel):
    train_id: str
    train_type: Literal["Passenger", "Express", "Freight"]
    current_pos: str
    delay: int
    buffer: int
    track_avail: Literal["Free", "Occupied"]
    stopping_pattern: Literal["All Stops", "Skip"]
    section_type: Literal["Double-line", "Single-line"]
    speed_limit: int

class RescheduleResponse(BaseModel):
    decision: str
    message: str

def get_state_from_input(train_type, track_avail, section_type, delay, buffer):
    return (
        train_type,
        track_avail,
        section_type,
        int(delay > 10),
        int(buffer < 10)
    )

def get_best_action(state):
    if state in Q:
        return actions[np.argmax(Q[state])]
    else:
        # fallback random action
        return np.random.choice(actions)

@router.post("/api/reschedule", response_model=RescheduleResponse)
async def reschedule(data: RescheduleRequest):
    state = get_state_from_input(
        data.train_type, data.track_avail, data.section_type, data.delay, data.buffer
    )
    decision = get_best_action(state)
    if decision == "Allow":
        message = f"Allow Train {data.train_id} to go first."
    elif decision == "Hold":
        message = f"Hold Train {data.train_id}."
    else:
        message = f"Reroute Train {data.train_id}."
    return RescheduleResponse(decision=decision, message=message)
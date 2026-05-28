from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from graph import tutor_graph, TutorState
from typing import Dict
import uvicorn
import json
from configuration import config
import random_lesson_gen
app = FastAPI()

# ── In-memory stores ───────────────────────────────────────────────────────────
# These are lightweight now — no Student/Assessor objects, just metadata

learning_objectives_store: Dict[str, dict] = {
    "science101": {
        "title": "Introduction to planets",
        "objectives": [
            "Understand the number of planets in the solar system",
            "Know the largest planet",
            "Know the smallest planet",
            "Demonstrate understanding of an orbit",
        ],
    }
}

# Maps student_id → lesson_id (replaces active_students objects)
student_registry: Dict[str, str] = {}

# Maps lesson_id → [student_ids]
active_rosters: Dict[str, list] = {}


# ── Learning Objectives ────────────────────────────────────────────────────────
@app.get("/api/generate-objectives")
async def generate_objectives(age: int, genre: str):
    result = random_lesson_gen.run_graph(age, genre)
    return result




@app.post("/api/learning-objectives")
async def add_learning_objectives(request: Request):
    data = await request.json()
    for field in ["lesson_id", "title", "objectives"]:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field '{field}'")
    if not isinstance(data["objectives"], list) or not all(isinstance(o, str) for o in data["objectives"]):
        raise HTTPException(status_code=400, detail="'objectives' must be a list of strings")

    learning_objectives_store[data["lesson_id"]] = {
        "title": data["title"],
        "objectives": data["objectives"],
    }
    return {"message": f"Learning objectives for '{data['lesson_id']}' received", "count": len(data["objectives"])}


@app.get("/api/learning-objectives")
async def get_learning_objectives():
    return learning_objectives_store


# ── Student Management ─────────────────────────────────────────────────────────

@app.post("/api/create-student")
async def create_student(request: Request):
    data = await request.json()
    for field in ["user_id", "lesson_id"]:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field '{field}'")
    if data["lesson_id"] not in learning_objectives_store:
        raise HTTPException(status_code=404, detail="Lesson not found")

    user_id, lesson_id = data["user_id"], data["lesson_id"]
    student_registry[user_id] = lesson_id
    active_rosters.setdefault(lesson_id, []).append(user_id)
    return {"message": f"Student {user_id} created"}


@app.get("/api/get-students")
async def get_students():
    return {"students": list(student_registry.keys())}


@app.get("/api/get-roster/{lesson_id}")
async def get_roster(lesson_id: str):
    if lesson_id not in active_rosters:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"roster": active_rosters[lesson_id]}


# ── Assessment ─────────────────────────────────────────────────────────────────

@app.get("/api/performance/{user_id}")
async def get_performance(user_id: str):
    """Returns the most recent assessment for a student from checkpointed state."""
    if user_id not in student_registry:
        raise HTTPException(status_code=404, detail="Student not found")

    config = {"configurable": {"thread_id": user_id}}
    state = tutor_graph.get_state(config)

    if not state or not state.values.get("assessment"):
        return {"message": "No assessments found for student."}
    print(state.values['assessment'])
    return {
        "student_id": user_id,
        "assessment": state.values["assessment"],
        "mastered": state.values["mastered"],
    }


# ── WebSocket Chat ─────────────────────────────────────────────────────────────

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    await websocket.accept()

    if user_id not in student_registry:
        await websocket.send_text("Student not found")
        await websocket.close()
        return

    lesson_id = student_registry[user_id]
    objectives = learning_objectives_store[lesson_id]["objectives"]
    config = {"configurable": {"thread_id": user_id}}

    # Seed initial state for this thread if it's a new session
    existing = tutor_graph.get_state(config)
    if not existing or not existing.values:
        tutor_graph.update_state(config, {
            "messages": [],
            "student_id": user_id,
            "lesson_id": lesson_id,
            "objectives": objectives,
            "assessment": {},
            "mastered": False,
        })

    try:
        while True:
            message = await websocket.receive_text()
            # Check if already mastered before processing
            state = tutor_graph.get_state(config)
            if state and state.values.get("mastered"):
                await websocket.send_text("🎉 All objectives mastered! Session complete.")
                break

            # Only pass the new user message — checkpointer supplies the rest
            result = tutor_graph.invoke(
                {"messages": [{"role": "user", "content": message}]},
                config=config,
            )

            # Send teacher's reply back to student
            teacher_reply = result["messages"][-1]["content"]
            await websocket.send_text(teacher_reply)

            # Notify if just mastered
            if result.get("mastered"):
                await websocket.send_text("🎉 All objectives mastered! Session complete.")
                break

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user: {user_id}")



if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
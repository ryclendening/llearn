from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv

load_dotenv()

from graph import tutor_graph, TutorState
from sqlalchemy.orm import Session
import uvicorn
import random_lesson_gen
import models
from crud import (
    add_message,
    create_chat_session,
    create_student_enrollment,
    get_latest_assessment,
    get_lesson,
    get_roster as get_roster_from_db,
    get_student,
    get_student_lesson_id,
    lesson_to_payload,
    list_lessons,
    list_student_ids,
    save_assessment,
    seed_default_lesson,
    upsert_lesson,
)
from database import Base, SessionLocal, engine, get_db

app = FastAPI()


@app.on_event("startup")
def initialize_database():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_default_lesson(db)


# ── Learning Objectives ────────────────────────────────────────────────────────
@app.get("/api/generate-objectives")
async def generate_objectives(age: int, genre: str):
    result = random_lesson_gen.run_graph(age, genre)
    return result




@app.post("/api/learning-objectives")
async def add_learning_objectives(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    for field in ["lesson_id", "title", "objectives"]:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field '{field}'")
    if not isinstance(data["objectives"], list) or not all(isinstance(o, str) for o in data["objectives"]):
        raise HTTPException(status_code=400, detail="'objectives' must be a list of strings")

    upsert_lesson(
        db,
        lesson_id=data["lesson_id"],
        title=data["title"],
        objectives=data["objectives"],
    )
    return {"message": f"Learning objectives for '{data['lesson_id']}' received", "count": len(data["objectives"])}


@app.get("/api/learning-objectives")
async def get_learning_objectives(db: Session = Depends(get_db)):
    return {lesson.id: lesson_to_payload(lesson) for lesson in list_lessons(db)}


# ── Student Management ─────────────────────────────────────────────────────────

@app.post("/api/create-student")
async def create_student(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    for field in ["user_id", "lesson_id"]:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field '{field}'")
    try:
        create_student_enrollment(db, student_id=data["user_id"], lesson_id=data["lesson_id"])
    except ValueError:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"message": f"Student {data['user_id']} created"}


@app.get("/api/get-students")
async def get_students(db: Session = Depends(get_db)):
    return {"students": list_student_ids(db)}


@app.get("/api/get-roster/{lesson_id}")
async def get_roster(lesson_id: str, db: Session = Depends(get_db)):
    roster = get_roster_from_db(db, lesson_id)
    if roster is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"roster": roster}


# ── Assessment ─────────────────────────────────────────────────────────────────

@app.get("/api/performance/{user_id}")
async def get_performance(user_id: str, db: Session = Depends(get_db)):
    """Returns the most recent persisted assessment for a student."""
    if not get_student(db, user_id):
        raise HTTPException(status_code=404, detail="Student not found")

    assessment = get_latest_assessment(db, user_id)
    if not assessment:
        return {"message": "No assessments found for student."}

    return {
        "student_id": user_id,
        "assessment": assessment.scores,
        "mastered": assessment.mastered,
    }


# ── WebSocket Chat ─────────────────────────────────────────────────────────────

@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    await websocket.accept()

    db = SessionLocal()
    try:
        lesson_id = get_student_lesson_id(db, user_id)
        if not lesson_id:
            await websocket.send_text("Student not found")
            await websocket.close()
            return

        lesson = get_lesson(db, lesson_id)
        if not lesson:
            await websocket.send_text("Lesson not found")
            await websocket.close()
            return

        objectives = [objective.text for objective in lesson.objectives]
        chat_session = create_chat_session(db, student_id=user_id, lesson_id=lesson_id)
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
                add_message(db, chat_session_id=chat_session.id, role="user", content=message)
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
                add_message(db, chat_session_id=chat_session.id, role="assistant", content=teacher_reply)
                if result.get("assessment"):
                    save_assessment(
                        db,
                        student_id=user_id,
                        lesson_id=lesson_id,
                        scores=result["assessment"],
                        mastered=bool(result.get("mastered")),
                    )
                await websocket.send_text(teacher_reply)

                # Notify if just mastered
                if result.get("mastered"):
                    await websocket.send_text("🎉 All objectives mastered! Session complete.")
                    break

        except WebSocketDisconnect:
            print(f"WebSocket disconnected for user: {user_id}")
    finally:
        db.close()



if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

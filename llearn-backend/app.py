from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from data import learning_objectives_store, active_assessors, active_students
import Assessor
import Student

app = FastAPI()
json_error = {"error": "Request must be JSON"}

@app.post("/api/learning-objectives")
async def add_learning_objectives(request: Request):
    data = await request.json()
    required_fields = ["lesson_id", "title", "objectives"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field '{field}'")

    if not isinstance(data["objectives"], list):
        raise HTTPException(status_code=400, detail="'objectives' must be a list")

    for obj in data["objectives"]:
        if not isinstance(obj, str):
            raise HTTPException(status_code=400, detail="Each objective must be a string")

    lesson_id = data["lesson_id"]
    learning_objectives_store[lesson_id] = {
        "title": data["title"],
        "objectives": data["objectives"]
    }

    return {"message": f"Learning objectives for lesson '{lesson_id}' received", "count": len(data["objectives"])}

@app.get("/api/learning-objectives")
async def get_learning_objectives():
    return learning_objectives_store

@app.post("/api/create-student")
async def create_student(request: Request):
    data = await request.json()
    required_fields = ["user_id", "lesson_id"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing required field '{field}'")

    active_students[data['user_id']] = Student.StudentChat(user_id=data['user_id'], lesson_id=data['lesson_id'])
    return {"message": f"Student {data['user_id']} created"}

@app.post("/api/create-assessor")
async def create_assessor(request: Request):
    data = await request.json()
    if "class_id" not in data:
        raise HTTPException(status_code=400, detail="Missing required field 'class_id'")

    class_id = data["class_id"]
    if class_id not in learning_objectives_store:
        raise HTTPException(status_code=404, detail="Class not found in learning objectives store")

    objectives = learning_objectives_store[class_id]["objectives"]
    active_assessors[class_id] = Assessor.AssessorChat(objectives=objectives, class_id=class_id)
    return {"message": f"Assessor for {class_id} created"}

@app.get("/api/performance/{user_id}")
async def get_performance(user_id: str):
    if user_id not in active_students:
        raise HTTPException(status_code=404, detail="Student not found")

    student = active_students[user_id]
    assessor = active_assessors[student.lesson_id]
    logs = assessor.session_logs

    for score in reversed(logs):
        if score["student_id"] == user_id:
            return score

    return {"message": "No assessments found for student."}

@app.get("/api/assess_performance/{user_id}")
async def assess_performance(user_id: str):
    student = active_students.get(user_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    assessor = active_assessors.get(student.lesson_id)
    if not assessor:
        raise HTTPException(status_code=404, detail="Assessor not found for student lesson")

    response = assessor.assess_performance(chat_history=student.chat_history, student_id=user_id)
    return {"response": response}


@app.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    await websocket.accept()
    if user_id not in active_students:
        await websocket.send_text("Student not found")
        await websocket.close()
        return

    student = active_students[user_id]
    try:
        while True:
            message = await websocket.receive_text()
            response = student.send_new_message(message)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user: {user_id}")
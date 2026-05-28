from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from db.crud import (
    add_message,
    create_chat_session,
    get_lesson,
    get_student_lesson_id,
    save_assessment,
)
from db.session import SessionLocal
from graph import tutor_graph


router = APIRouter(tags=["chat"])


@router.websocket("/ws/chat/{user_id}")
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

                state = tutor_graph.get_state(config)
                if state and state.values.get("mastered"):
                    await websocket.send_text("🎉 All objectives mastered! Session complete.")
                    break

                result = tutor_graph.invoke(
                    {"messages": [{"role": "user", "content": message}]},
                    config=config,
                )

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

                if result.get("mastered"):
                    await websocket.send_text("🎉 All objectives mastered! Session complete.")
                    break

        except WebSocketDisconnect:
            print(f"WebSocket disconnected for user: {user_id}")
    finally:
        db.close()

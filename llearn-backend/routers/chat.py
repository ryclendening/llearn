from __future__ import annotations

import json
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from db.crud import (
    add_message,
    create_chat_session,
    get_lesson,
    get_student_lesson_id,
    list_published_examples,
    save_assessment,
)
from db.session import SessionLocal
from graph import tutor_graph


router = APIRouter(tags=["chat"])


def _chat_payload(text: str, citations: list[dict] | None = None, message_type: str = "assistant") -> str:
    return json.dumps({
        "type": message_type,
        "text": text,
        "citations": citations or [],
    })


@router.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    await websocket.accept()

    db = SessionLocal()
    try:
        lesson_id = get_student_lesson_id(db, user_id)
        if not lesson_id:
            await websocket.send_text(_chat_payload("Student not found", message_type="system"))
            await websocket.close()
            return

        lesson = get_lesson(db, lesson_id)
        if not lesson:
            await websocket.send_text(_chat_payload("Lesson not found", message_type="system"))
            await websocket.close()
            return

        objectives = [objective.text for objective in lesson.objectives]
        protected_examples = [
            {
                "problem_text": item.example.problem_text,
                "solution_text": item.example.solution_text,
            }
            for item in (list_published_examples(db, lesson_id) or [])
        ]
        chat_session = create_chat_session(db, student_id=user_id, lesson_id=lesson_id)
        config = {"configurable": {"thread_id": user_id}}

        existing = tutor_graph.get_state(config)
        if not existing or not existing.values:
            tutor_graph.update_state(config, {
                "messages": [],
                "student_id": user_id,
                "lesson_id": lesson_id,
                "objectives": objectives,
                "assessment": {f"objective_{i+1}": 0 for i in range(len(objectives))},
                "mastered": False,
                "protected_examples": protected_examples,
            })
        else:
            tutor_graph.update_state(config, {
                "lesson_id": lesson_id,
                "objectives": objectives,
                "protected_examples": protected_examples,
            })

        try:
            while True:
                message = await websocket.receive_text()
                try:
                    add_message(db, chat_session_id=chat_session.id, role="user", content=message)

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
                    await websocket.send_text(_chat_payload(teacher_reply, result.get("citations", [])))

                    if result.get("mastered"):
                        await websocket.send_text(_chat_payload(
                            "All lesson objectives are mastered. You can keep asking questions or work on example problems.",
                            message_type="system",
                        ))
                except WebSocketDisconnect:
                    raise
                except Exception:
                    db.rollback()
                    traceback.print_exc()
                    await websocket.send_text(_chat_payload(
                        "I hit an error while processing that message. Please try again.",
                        message_type="system",
                    ))

        except WebSocketDisconnect:
            print(f"WebSocket disconnected for user: {user_id}")
    finally:
        db.close()

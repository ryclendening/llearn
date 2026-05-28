import json
import openai
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


# ── State ──────────────────────────────────────────────────────────────────────

class TutorState(TypedDict):
    messages: Annotated[list, operator.add]   # auto-appends on every update
    student_id: str
    lesson_id: str
    objectives: list[str]
    assessment: dict        # {"objective_1": 0, "objective_2": 1, ...}
    mastered: bool


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_objective_list(objectives: list[str]) -> str:
    return "\n".join(f"objective_{i+1}: {obj}" for i, obj in enumerate(objectives))

def _teacher_system_prompt(objectives: list[str]) -> str:
    return (
        f"You are an intelligent assistant focused on teaching a 4th grade student "
        f"about the following objectives: {', '.join(objectives)}. "
        f"Do not let the user derail the conversation and make sure they learn these "
        f"objectives. But don't give them the answers."
    )


# ── Nodes ──────────────────────────────────────────────────────────────────────

def teacher_node(state: TutorState) -> dict:
    """Responds to the student, guided by the lesson objectives."""
    system = {"role": "system", "content": _teacher_system_prompt(state["objectives"])}
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[system] + state["messages"],
        temperature=0.2,
    )
    reply = (response.choices[0].message.content or "").strip()
    return {"messages": [{"role": "assistant", "content": reply}]}


def assessor_node(state: TutorState) -> dict:
    """Incrementally updates student understanding after the latest exchange."""
    objective_list = _build_objective_list(state["objectives"])
    previous_assessment = _normalize_assessment(state.get("assessment", {}), len(state["objectives"]))
    latest_exchange = state["messages"][-2:]
    system = {
        "role": "system",
        "content": (
            "You update a student's mastery assessment after each tutoring exchange. "
            "Use the previous assessment as the baseline. Only change an objective from 0 to 1 "
            "when the latest exchange gives clear evidence that the student understands it. "
            "Do not change a mastered objective back to 0 unless the latest exchange clearly "
            "shows the previous mastery was wrong. Return JSON only."
        ),
    }
    prompt = {
        "role": "user",
        "content": (
            f"Objectives:\n{objective_list}\n\n"
            f"Previous assessment:\n{json.dumps(previous_assessment)}\n\n"
            f"Latest exchange:\n{json.dumps(latest_exchange)}\n\n"
            "Return ONLY a JSON object mapping every objective key to 1 or 0."
        ),
    }
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[system, prompt],
        temperature=0.1,
    )
    raw = (response.choices[0].message.content or "").strip()
    try:
        # Strip markdown code fences if present
        clean = raw.replace("```json", "").replace("```", "").strip()
        assessment = _normalize_assessment(json.loads(clean), len(state["objectives"]))
    except json.JSONDecodeError:
        # Keep the last known assessment rather than erasing progress on parser failure.
        assessment = previous_assessment

    mastered = bool(assessment) and all(v == 1 for v in assessment.values())
    return {"assessment": assessment, "mastered": mastered}


def _normalize_assessment(assessment: dict, objective_count: int) -> dict:
    normalized = {}
    for i in range(objective_count):
        key = f"objective_{i+1}"
        normalized[key] = 1 if assessment.get(key) in (1, True, "1") else 0
    return normalized


# ── Routing ────────────────────────────────────────────────────────────────────

def should_continue(state: TutorState) -> str:
    return "mastered" if state["mastered"] else "continue"


# ── Graph ──────────────────────────────────────────────────────────────────────

def build_graph(checkpointer=None):
    graph = StateGraph(TutorState)

    graph.add_node("teacher", teacher_node)
    graph.add_node("assessor", assessor_node)

    graph.set_entry_point("teacher")
    graph.add_edge("teacher", "assessor")
    graph.add_conditional_edges(
        "assessor",
        should_continue,
        {
            "continue": END,    # wait for next student message
            "mastered": END,    # session complete — app layer handles the distinction
        },
    )

    return graph.compile(checkpointer=checkpointer or MemorySaver())


# Shared compiled graph — one instance for the whole app
tutor_graph = build_graph()

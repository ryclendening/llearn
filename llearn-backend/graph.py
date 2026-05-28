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
        temperature=0.5,
    )
    reply = (response.choices[0].message.content or "").strip()
    return {"messages": [{"role": "assistant", "content": reply}]}


def assessor_node(state: TutorState) -> dict:
    """Silently evaluates student understanding after every teacher response."""
    objective_list = _build_objective_list(state["objectives"])
    system = {
        "role": "system",
        "content": (
            "Assess the student's performance based on the given objectives. "
            "Return a JSON object ONLY, with 1 for understood and 0 for not understood: "
            '{"objective_1": 0, "objective_2": 1, ...}'
        ),
    }
    prompt = {
        "role": "user",
        "content": (
            f"Objectives:\n{objective_list}\n\n"
            f"Conversation:\n{state['messages']}\n\n"
            "Return ONLY a JSON object mapping each objective key to 1 or 0."
        ),
    }
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[system, prompt],
        temperature=0.2,
    )
    raw = (response.choices[0].message.content or "").strip()
    try:
        # Strip markdown code fences if present
        clean = raw.replace("```json", "").replace("```", "").strip()
        assessment = json.loads(clean)
    except json.JSONDecodeError:
        # Fall back to all zeros — don't crash the session
        assessment = {f"objective_{i+1}": 0 for i in range(len(state["objectives"]))}

    mastered = bool(assessment) and all(v == 1 for v in assessment.values())
    return {"assessment": assessment, "mastered": mastered}


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

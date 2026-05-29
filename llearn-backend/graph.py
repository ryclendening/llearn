import json
import openai
import re
from functools import lru_cache
from numbers import Number
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from sentence_transformers import SentenceTransformer
from vector_db.pipeline import EMBED_MODEL
from vector_db.vector_store import SearchResult, get_vector_db

# ── State ──────────────────────────────────────────────────────────────────────

RETRIEVAL_TOP_K = 4
RETRIEVAL_FALLBACK_K = 12
CITATION_SNIPPET_LENGTH = 700

class TutorState(TypedDict):
    messages: Annotated[list, operator.add]   # auto-appends on every update
    student_id: str
    lesson_id: str
    grade: int
    objectives: list[str]
    assessment: dict        # {"objective_1": 0, "objective_2": 1, ...}
    mastered: bool
    retrieved_context: str
    retrieved_sources: list[dict]
    citations: list[dict]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_objective_list(objectives: list[str]) -> str:
    return "\n".join(f"objective_{i+1}: {obj}" for i, obj in enumerate(objectives))

@lru_cache(maxsize=1)
def _embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBED_MODEL)


def _latest_user_message(messages: list) -> str:
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            return str(message.get("content") or "").strip()
    return ""


def _format_retrieved_context(results: list[SearchResult]) -> tuple[str, list[dict]]:
    context_blocks = []
    sources = []
    for index, result in enumerate(results, start=1):
        properties = result.properties
        text = str(properties.get("text") or "").strip()
        if not text:
            continue

        source_id = f"source_{index}"
        page = _plain_int(properties.get("page"))
        material_id = _plain_int(properties.get("material_id"))
        distance = _plain_float(result.score)
        source = {
            "source_id": source_id,
            "chunk_id": result.uuid,
            "document_id": properties.get("document_id"),
            "page": page,
            "class_id": properties.get("class_id"),
            "material_id": material_id,
            "distance": distance,
            "snippet": text[:CITATION_SNIPPET_LENGTH],
        }
        sources.append(source)

        metadata = [
            f"Source id: [{source_id}]",
            f"Document id: {source['document_id'] or 'unknown'}",
            f"Page: {page or 'unknown'}",
            f"Material id: {material_id or 'unknown'}",
        ]
        context_blocks.append("\n".join(metadata) + f"\nText:\n{text}")

    return "\n\n".join(context_blocks), sources


def _plain_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _plain_float(value) -> float | None:
    if value is None:
        return None
    if not isinstance(value, Number):
        return None
    return float(value)


def _citations_for_reply(reply: str, sources: list[dict]) -> list[dict]:
    cited_ids = set(re.findall(r"\[(source_\d+)\]", reply))
    return [source for source in sources if source.get("source_id") in cited_ids]


def _retrieve_lesson_context(query: str, lesson_id: str) -> tuple[str, list[dict]]:
    if not query or not lesson_id:
        return "", []

    db = get_vector_db()
    try:
        query_vector = _embedding_model().encode([query], show_progress_bar=False)[0].tolist()
        try:
            results = db.similarity_search(
                query_vector=query_vector,
                k=RETRIEVAL_TOP_K,
                filters={db.class_id_key: lesson_id},
            )
        except Exception as exc:
            print(f"Filtered context retrieval skipped for lesson '{lesson_id}': {exc}")
            results = []

        if not results:
            fallback_results = db.similarity_search(query_vector=query_vector, k=RETRIEVAL_FALLBACK_K)
            results = [
                result
                for result in fallback_results
                if result.properties.get(db.class_id_key) == lesson_id
                or str(result.properties.get(db.document_id_key) or "").startswith(f"{lesson_id}:")
            ][:RETRIEVAL_TOP_K]

        return _format_retrieved_context(results)
    except Exception as exc:
        print(f"Context retrieval skipped for lesson '{lesson_id}': {exc}")
        return "", []
    finally:
        db.close()


def _teacher_system_prompt(objectives: list[str], retrieved_context: str, grade: int) -> str:
    return (
        f"You are an intelligent assistant focused on teaching a {grade} grade student.\n\n"
        "Your job is to teach the student the lesson objectives using the provided "
        "class material when relevant.\n\n"
        "Rules:\n"
        "- Keep the conversation focused on the lesson objectives.\n"
        "- Do not let the student derail the lesson.\n"
        "- Do not give away final answers directly.\n"
        "- Use hints, guiding questions, examples, and checks for understanding.\n"
        "- Use the class material as the source of truth when it is relevant.\n"
        "- If the retrieved class material is not relevant, do not force it.\n"
        "- Do not invent facts and imply they came from the class material.\n\n"
        "Citation rules:\n"
        "- When you use retrieved class material, cite it inline with its source id, like [source_1].\n"
        "- Only cite source ids that appear in the retrieved class material below.\n"
        "- Do not cite a source unless it directly supports the sentence.\n"
        "- Do not invent page numbers, source ids, or document details.\n\n"
        f"Lesson objectives:\n{_build_objective_list(objectives)}\n\n"
        f"Retrieved class material:\n"
        f"{retrieved_context or '[No relevant class material retrieved.]'}"
    )

# ── Nodes ──────────────────────────────────────────────────────────────────────

def retrieve_context_node(state: TutorState) -> dict:
    """Retrieves lesson-specific class material relevant to the latest student message."""
    query = _latest_user_message(state.get("messages", []))
    context, sources = _retrieve_lesson_context(query, state.get("lesson_id", ""))
    return {"retrieved_context": context, "retrieved_sources": sources}


def teacher_node(state: TutorState) -> dict:
    """Responds to the student, guided by the lesson objectives."""
    system = {
        "role": "system",
        "content": _teacher_system_prompt(
            state["objectives"],
            state.get("retrieved_context", ""),
            state.get("grade", 8),
        ),
    }
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[system] + state["messages"],
        temperature=0.2,
    )
    reply = (response.choices[0].message.content or "").strip()
    return {
        "messages": [{"role": "assistant", "content": reply}],
        "citations": _citations_for_reply(reply, state.get("retrieved_sources", [])),
    }


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

    graph.add_node("retrieve_context", retrieve_context_node)
    graph.add_node("teacher", teacher_node)
    graph.add_node("assessor", assessor_node)

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "teacher")
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

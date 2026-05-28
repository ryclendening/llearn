import json
import openai
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field, ValidationError
from typing import List
from configuration import config as app_config

class LearningObjectives(BaseModel):
    lesson_id: str
    title: str
    objectives: List[str] = Field(min_length=3, max_length=6)

class Generator(TypedDict):
    messages: Annotated[list, operator.add]
    age: int
    genre: str
    lesson_plan: str
    valid: bool

def _generator_system_prompt(genre: str, age: int) -> str:
    return (
        f"You are an intelligent assistant and need to come up with discrete learning objectives for "
        f"students at age {age} and on the topic of {genre}. "
        f"You must generate at least 3, but no more than 6 objectives. "
        f"Return ONLY raw JSON with no markdown, no backticks, no explanation, just the JSON object itself."
        f"{{'lesson_id': 'class123', 'title': 'classtitle', 'objectives': ['objective 1', 'objective 2', ...]}}. "
    )

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

llm = ChatOpenAI(model="gpt-4o")
structured_llm = llm.with_structured_output(LearningObjectives)

def generator_node(state: Generator):
    system = SystemMessage(content=_generator_system_prompt(state["genre"], state['age']))
    response = structured_llm.invoke([system] + state["messages"])
    # response is already a LearningObjectives pydantic object
    return {"lesson_plan": response.model_dump()}

def validate_formatting(state: Generator):
    try:
        LearningObjectives(**state["lesson_plan"])
        return {"valid": True}
    except ValidationError as e:
        print("[validator] failed:", e)
        return {"valid": False}

def should_continue(state: Generator) -> str:
    return "PASSED" if state["valid"] else "FAILED"

def build_graph(checkpointer=None):
    graph = StateGraph(Generator)
    graph.add_node("generator", generator_node)
    graph.add_node("validator", validate_formatting)
    graph.set_entry_point("generator")
    graph.add_edge("generator", "validator")
    graph.add_conditional_edges(
        "validator",
        should_continue,
        {"FAILED": "generator", "PASSED": END},
    )
    return graph.compile(checkpointer=checkpointer or MemorySaver())



def run_graph(age: int, genre: str):
    gen_graph = build_graph()
    config = {"configurable": {"thread_id": "test_session"}}
    result = gen_graph.invoke(
        {"messages": [], "age": age, "genre": genre, "lesson_plan": "", "valid": False},
        config=config,
    )
    print("Valid:", result["valid"])
    print("Lesson Plan:", result["lesson_plan"])
    return result["lesson_plan"]
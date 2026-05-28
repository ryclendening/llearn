from Student import StudentChat
from Assessor import AssessorChat
from typing import Dict
learning_objectives_store = {
  "science101": {
    "title": "Introduction to plants",
    "objectives": [
      "Understand the number of planet's in the solar system",
      "Know the largest planet",
      "Know the smallest planet",
      "Demonstrate understanding of an orbit"
    ]
  }
}

active_students: Dict[str, StudentChat] = {}
active_assessors: Dict[str, AssessorChat] = {}
active_rosters: Dict[str, list] = {}

active_students = {}
active_assessors = {}
active_rosters={}
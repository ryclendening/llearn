import configuration.config as config
import json
import openai
from datetime import datetime

class AssessorChat:
    """
    Represents a teacher who interacts with a student through a chat interface.
    """

    def __init__(self, objectives,class_id):
        self.session_logs = []
        self.active_users = []
        self.class_id = class_id
        self.objectives = objectives

        # System prompt to set the assistant's behavior
        self.system_prompt = {
            "role": "system",
            "content": (
                "Assess the student's performance (defined as user) based on the following objectives: "
                "Return a JSON object in this format only, with 1 signifying understanding of objective, "
                "and 0 representing that a user doesn't understand: "
                '{"objective_1": 0, "objective_2": 1, ..., "objective_n": 0}'
                )
        }

    def assess_performance(self, chat_history, student_id):
        objective_keys = [f"objective_{i+1}" for i in range(len(self.objectives))]
        objective_list = "\n".join([f"{k}: {obj}" for k, obj in zip(objective_keys, self.objectives)])

        assessment_prompt = {
            "role": "user",
            "content": (
                f"Assess the student's performance based on the following objectives:\n{objective_list}\n\n"
                f"Conversation:\n{chat_history}\n\n"
                f"Return ONLY a JSON object mapping each objective key to 1 (understood) or 0 (not understood)."
            )
        }

        messages = [self.system_prompt]+[assessment_prompt]

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages, # type: ignore
            temperature=0.2
        )

        result = response.choices[0].message.content or ''
        result = result.strip()

        try:
            parsed_result = json.loads(result)
        except json.JSONDecodeError:
            parsed_result = None

        self.session_logs.append({ # TODO: Go back and fix the session logging to enhance scalability
            "user_id": student_id,
            "timestamp": datetime.now(),
            "raw_message": result,
            "parsed_message": parsed_result
        })

        return parsed_result

    def display_logs(self):
        """
        Displays the conversation logs.
        """
        for msg in self.session_logs:
            print(msg, "\n")

    def display_most_recent(self):
        """
        Displays the most recent message in the conversation logs.
        """
        print(self.session_logs[-1])

    def get_obj_dict(self):
        """
        Parses and returns the JSON object of assessed objectives.
        """
        return json.loads(self.session_logs[-1]['message'])

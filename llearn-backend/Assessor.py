import configuration.config as config
import json
import openai

class AssessorChat:
    """
    Represents a teacher who interacts with a student through a chat interface.
    """

    def __init__(self, objectives):
        self.session_logs = []
        self.active_users = []
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
        """
        Assesses the performance of the student based on objectives.
        Sends chat history to GPT and appends the response.
        """
        assessment_prompt = {
            "role": "user",
            "content": (
                f"Assess the student's performance defined as user) based on the following objectives: "
                f"{', '.join(self.objectives)}.\n\n"
                f"Conversation:\n{chat_history}\n\n"
                f"Return a JSON object in this format only, with 1 siginfying understanding of objective, and 0 representing that a user doesn't understand: "
                f'{{"objective_1": 0, "objective_2": 1, ..., "objective_n": 0}}'
            )
        }

        messages = [self.system_prompt] + [assessment_prompt]

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages, # type: ignore
            temperature=0.2
        )
        
        result = response.choices[0].message.content
        if result is None:
            result = ''
        else:
            result=result.strip()
        print(result)
        self.session_logs.append({"student_id":student_id, "message": result})

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

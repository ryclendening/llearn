import configuration.config as config
import openai
import app

class StudentChat:
    """
    Represents a student who interacts with a teacher through a chat interface.
    """

    def __init__(self, user_id, lesson_id):
        """
        Initializes a StudentChat object.

        Args:
            user_id (str): The ID of the student.
        """
        self.user_id = user_id
        self.lesson_id = lesson_id
        self.objectives = app.learning_objectives_store[lesson_id]['objectives']
        self.session_logs = []       # logs of the conversation
        self.chat_history = []       # messages for the chat completions API
        # System prompt to guide assistant behavior (optional)
        self.system_prompt = {
            "role": "system",
            'content':f"You are a intelligent assistant, but are focusing on teaching a 4th grade student about the following objectives {','.join(self.objectives)}. Do not let the user derail the conversation and make sure they learn these objectives. But don't give them the answers",
        }
        self.chat_history.append(self.system_prompt)

    def send_new_message(self, stud_text: str):
        """
        Sends a new message from the student to the assistant and gets a reply.

        Args:
            stud_text (str): The text of the student's message.
        """
        # Add the student's message to history
        self.chat_history.append({"role": "user", "content": stud_text})
        self.session_logs.append({"role": "user", "message": stud_text})

        # Call OpenAI Chat Completion API
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=self.chat_history, # type: ignore
            temperature=0.5,
        )

        # Safely get assistant response content and strip it
        result = response.choices[0].message.content
        if result is None:
            result = ''
        else:
            result=result.strip()
        # Add assistant's reply to history and logs
        self.chat_history.append({"role": "assistant", "content": result})
        self.session_logs.append({"role": "assistant", "message": result})

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
        if self.session_logs:
            print(self.session_logs[-1])
        else:
            print("No conversation logs yet.")

    def clear_conversation(self):
        """
        Clears the conversation history.
        """
        self.session_logs = []
        self.chat_history = [self.system_prompt]
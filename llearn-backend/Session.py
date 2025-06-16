import configuration.config as config
import json

class ChatSession:
    """
    Represents a teacher who interacts with a student through a chat interface.
    """

    def __init__(self, teacher_id, assistant, objectives):
        """
        Initializes a Teacher object.

        Args:
            teacher_id (str): The ID of the teacher.
            assistant (openai.Assistant): The OpenAI assistant used for communication.
            objectives (list): The objectives that the teacher is trying to teach.
        """
        self.user_id = teacher_id
        self.sesion_id = None
        self.assistant = assistant
        self.session_logs = []
        self.active_users = [] # number of active users in the session
        self.objectives = objectives # class objectives that the teacher is trying to teach


    def pull_logs(self, thread_id):
        """
        Pulls the conversation logs from a thread.

        Args:
            thread_id (str): The ID of the thread.

        Returns:
            list: The conversation logs.
        """
        stud_convo = config.client.beta.threads.messages.list(thread_id)
        return stud_convo

    def create_thread(self):
        """
        Creates a new thread for the student to use.
        """
        self.thread = config.client.beta.threads.create()
import configuration.config as config
import json

class TeacherChat:
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

    def assess_performance(self, thread_id):
        """
        Assesses the performance of the student based on the objectives set by the teacher.

        Args:
            stud_text (str): The text of the student's message.

        Returns:
            dict: The student's progress in understanding the objectives.
        """
        logs = config.client.beta.threads.messages.list(thread_id=thread_id)
        print('formated logs',self.format_logs_for_prompt(logs))
        config.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=self.format_logs_for_prompt(logs))
        run = config.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            instructions=f'You are assessing the students performance related the following objectives {",".join(self.objectives)}. Only assess the users progress, (depicted as user in the attached message) in understanding the objectives in the following dict format (where 0 means not achieved and 1 means achieved): {{"objective_1": 0, "objective_2": 0, ... "objective_n":0}}. Do not return anything but the specified format.')
        if run.status =='failed':
            print("Error:", run.last_error)
        if run.status == "completed":
            messages = config.client.beta.threads.messages.list(thread_id=self.thread.id)
            message = messages.data[0]
            assert message.content[0].type == "text"
            self.session_logs.append({"role": message.role, "message": message.content[0].text.value})
            
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
        Retrieves the objectives dictionary from the conversation logs.

        Returns:
            dict: The objectives dictionary.
        """
        return json.loads(self.session_logs[-1]['message'])

    def delete_thread(self):
        """
        Deletes the thread.
        """
        config.client.beta.threads.delete(self.thread.id)

    def format_logs_for_prompt(self,logs):
        formatted = []
        for message in reversed(logs.data):  # Reverse to get chronological order
            if message.content and message.content[0].type == "text":
                role = message.role.capitalize()
                text = message.content[0].text.value.strip()
                formatted.append(f"{role}: {text}")
        return "\n".join(formatted)
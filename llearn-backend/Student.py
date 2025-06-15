import configuration.config as config


class StudentChat:
    """
    Represents a student who interacts with a teacher through a chat interface.
    """

    def __init__(self, user_id, assistant):
        """
        Initializes a StudentChat object.

        Args:
            user_id (str): The ID of the student.
            assistant (openai.Assistant): The OpenAI assistant used for communication.
        """
        self.user_id = user_id
        self.sesion_id = None
        self.assistant = assistant
        self.session_logs = []

    def create_thread(self):
        """
        Creates a new thread for the student to use.
        """
        self.thread = config.client.beta.threads.create()

    def send_new_message(self, stud_text):
        """
        Sends a new message from the student to the teacher.

        Args:
            stud_text (str): The text of the student's message.
        """
        self.session_logs.append({"role": 'user', "message": stud_text})
        config.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=stud_text, )
        run = config.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id)
        if run.status == 'failed':
            print("Error reason", run.last_error)
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

    def delete_thread(self):
        """
        Deletes the thread.
        """
        config.client.beta.threads.delete(self.thread.id)



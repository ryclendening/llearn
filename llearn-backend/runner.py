import pandas as pd
import os
import sys
import configuration.config as config
# Import the openai package
import openai
import requests
import json
from Student import StudentChat
from Teacher import TeacherChat


if __name__ == "__main__":
    client = openai.OpenAI(api_key=config.key_val)
    objectives = ['Students will know which planet is closest to the sun', 'students will know which planet is largest']
    assistant = client.beta.assistants.create(
        name="Math Tutor",
        instructions=f"You are a intelligent assistant, but are focusing on teaching a 4th grade student about the following objectives {','.join(objectives)}. Do not let the user derail the conversation and make sure they learn these objectives. But don't give them the answers",
        tools=[{"type": "code_interpreter"}],
        model="gpt-4-1106-preview",
    )
    test_teacher = TeacherChat(teacher_id='nfdgdg314', assistant=assistant, objectives=objectives)
    test_teacher.create_thread()
    test_student = StudentChat(user_id='nn243241s', assistant=assistant)
    test_student.create_thread()
    objectives_sat = {'objective_1': 0, 'objective_2': 0}
    test_student2 = StudentChat(user_id='nn243269x', assistant=assistant)
    test_student2.create_thread()


    while set(objectives_sat.values()).__contains__(0):  # while all goals have not been satisifed, continue
        new_msg = input('what would you like to say?\n')
        test_student.send_new_message(new_msg)
        test_student.display_most_recent()
        test_teacher.assess_performance(test_student.thread.id)
        test_teacher.display_most_recent()
        objectives_sat = test_teacher.get_obj_dict()
    print('STUDENT 1 is smart')


    objectives_sat = {'objective_1': 0, 'objective_2': 0}
    while set(objectives_sat.values()).__contains__(0):  # while all goals have not been satisifed, continue
        new_msg = input('what would you like to say?\n')
        test_student2.send_new_message(new_msg)
        test_student2.display_most_recent()
        test_teacher.assess_performance(test_student2.thread.id)
        test_teacher.display_most_recent()
        objectives_sat = test_teacher.get_obj_dict()

    test_teacher.delete_thread()
    test_student.delete_thread()
    test_student2.delete_thread()

    client.beta.assistants.delete(assistant.id)

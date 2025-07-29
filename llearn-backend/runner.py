import pandas as pd
import os
import sys
import configuration.config as config
# Import the openai package
import openai
import requests
import json
from Student import StudentChat
from Assessor import AssessorChat
from app import learning_objectives_store

if __name__ == "__main__":
    client = openai.OpenAI(api_key=config.key_val)
    objectives = learning_objectives_store['science101']['objectives']
    print(objectives)

    test_teacher = AssessorChat(objectives=objectives)
    test_student = StudentChat(user_id='nn243241s',lesson_id='science101')
    objectives_sat = {'objective_1': 0, 'objective_2': 0}
    test_student2 = StudentChat(user_id='nn243269x', lesson_id= 'science101')


    while set(objectives_sat.values()).__contains__(0):  # while all goals have not been satisifed, continue
        new_msg = input('what would you like to say?\n')
        test_student.send_new_message(new_msg)
        test_student.display_most_recent()
        test_teacher.assess_performance(test_student.chat_history)
        test_teacher.display_most_recent()
        objectives_sat = test_teacher.get_obj_dict()
    print('STUDENT 1 is smart')


    objectives_sat = {'objective_1': 0, 'objective_2': 0}
    while set(objectives_sat.values()).__contains__(0):  # while all goals have not been satisifed, continue
        new_msg = input('what would you like to say?\n')
        test_student2.send_new_message(new_msg)
        test_student2.display_most_recent()
        test_teacher.assess_performance(test_student2.chat_history,test_student2.student)
        test_teacher.display_most_recent()
        objectives_sat = test_teacher.get_obj_dict()
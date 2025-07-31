import requests

BASE_URL = "http://127.0.0.1:8000/api"

def assess_performance(user_id):
    print(f"Testing GET /assess_performance/{user_id}...")
    r = requests.get(f"{BASE_URL}/assess_performance/{user_id}")
    data = r.json()
    return data

def get_assessors():
    r = requests.get(f"{BASE_URL}/get-assessors/")
    print(r.status_code)
    data = r.json()
    return data

def create_assessor():
    print("Testing POST /create-assessor with valid data...")
    payload = {"class_id": "science101"}
    r = requests.post(f"{BASE_URL}/create-assessor", json=payload)
    return r.status_code

def create_student():
    payload = {"user_id": "test_tickle69", "lesson_id": "science101"}
    r = requests.post(f"{BASE_URL}/create-student", json=payload)
    return r.status_code

def get_roster(lesson_id):
    r = requests.get(f"{BASE_URL}/get-roster/{lesson_id}")
    return r.json()

def get_students():
    r = requests.get(f"{BASE_URL}/get-students")
    return r.json()
if __name__ == '__main__':
    #create_assessor()
    print(get_assessors())
    # students= get_roster('science101')['roster']
    # for stud in students:
    #     print(stud)
    #     print(assess_performance(stud))
    # print(get_students())
    #print(assess_performance('user_1753924954690'))

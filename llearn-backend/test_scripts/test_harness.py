import requests

BASE_URL = "http://127.0.0.1:8000/api"

def assess_performance(user_id):
    print(f"Testing GET /assess_performance/{user_id}...")
    r = requests.get(f"{BASE_URL}/assess_performance/{user_id}")
    data = r.json()
    print(data)

def get_assessors():
    r = requests.get(f"{BASE_URL}/get-assessors/")
    print(r.status_code)
    data = r.json()
    print(data)

def create_assessor():
    print("Testing POST /create-assessor with valid data...")
    payload = {"class_id": "science101"}
    r = requests.post(f"{BASE_URL}/create-assessor", json=payload)

if __name__ == '__main__':
    #create_assessor()
    #get_assessors()
    assess_performance('user_1753843129883')

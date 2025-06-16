import requests
import json

url = "http://127.0.0.1:5000/api/learning-objectives"
data = {
    "lesson_id": "science101",
    "title": "Introduction to plants",
    "objectives": ["Understand the number of planets in the solar system",
                   "Know the largest planet",
                   "Know the smallest planet",
                   "Demonstrate understanding of an orbit"
    ]
}

headers = {"Content-Type": "application/json"}

response = requests.post(url, data=json.dumps(data), headers=headers)
response = requests.get(url, headers=headers)
print("Status code:", response.status_code)
print("Response JSON:", response.json())
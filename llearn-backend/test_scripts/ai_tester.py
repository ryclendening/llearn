import requests
import websockets
import asyncio


BASE_URL = "http://127.0.0.1:8000/api"
BASE_WS_URL = "ws://127.0.0.1:8000/ws/chat"

def test_learning_objectives():
    print("Testing POST /learning-objectives with valid data...")
    payload = {
        "lesson_id": "science101",
        "title": "Introduction to plants",
        "objectives": [
            "Understand the number of planets in the solar system",
            "Know the largest planet",
            "Know the smallest planet",
            "Demonstrate understanding of an orbit"
        ]
    }
    r = requests.post(f"{BASE_URL}/learning-objectives", json=payload)
    assert r.status_code == 200, r.text
    print("POST /learning-objectives passed.")

    print("Testing GET /learning-objectives...")
    r = requests.get(f"{BASE_URL}/learning-objectives")
    assert r.status_code == 200, r.text
    data = r.json()
    print(data)
    assert "science101" in data, "science101 missing from learning objectives"
    print("GET /learning-objectives passed.")


def test_create_student():
    print("Testing POST /create-student with valid data...")
    payload = {"user_id": "student1", "lesson_id": "science101"}
    r = requests.post(f"{BASE_URL}/create-student", json=payload)
    assert r.status_code == 200, r.text
    print("POST /create-student passed.")


def test_create_assessor():
    print("Testing POST /create-assessor with valid data...")
    payload = {"class_id": "science101"}
    r = requests.post(f"{BASE_URL}/create-assessor", json=payload)
    assert r.status_code == 200, r.text
    print("POST /create-assessor passed.")




async def test_submit_chat_via_websocket(message):
    uri = f"{BASE_WS_URL}/student1"
    print(f"Connecting to WebSocket at {uri}...")

    async with websockets.connect(uri) as websocket:
        print("Connected. Sending message...")
        await websocket.send(message)

        response = await websocket.recv()
        print("Received:", response)

        assert response is not None
        print("WebSocket chat submission passed.")

def test_assess_performance():
    print("Testing GET /assess_performance/student1...")
    r = requests.get(f"{BASE_URL}/assess_performance/student1")
    assert r.status_code == 200, r.text
    data = r.json()
    print("Assess performance response:", data)
    assert "response" in data
    print("GET /assess_performance passed.")

def test_get_performance():
    print("Testing GET /performance/student1...")
    r = requests.get(f"{BASE_URL}/performance/student1")
    # This may return 404 if no assessments have been logged yet.
    if r.status_code == 404:
        print("No performance data found yet (expected if no assessments run).")
    else:
        assert r.status_code == 200, r.text
        data = r.json()
        print("Performance data:", data)
    print("GET /performance passed.")

if __name__ == "__main__":
    test_learning_objectives()
    test_create_student()
    test_create_assessor()
    asyncio.run(test_submit_chat_via_websocket('hello there'))
    test_assess_performance()
    test_get_performance()

    print("All tests done.")
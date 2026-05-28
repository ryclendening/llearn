import requests
import websockets
import asyncio

BASE_URL = "http://127.0.0.1:8000/api"
BASE_WS_URL = "ws://127.0.0.1:8000/ws/chat"


def test_learning_objectives():
    print("\n── POST /learning-objectives ──")
    payload = {
        "lesson_id": "science101",
        "title": "Introduction to planets",
        "objectives": [
            "Understand the number of planets in the solar system",
            "Know the largest planet",
            "Know the smallest planet",
            "Demonstrate understanding of an orbit",
        ],
    }
    r = requests.post(f"{BASE_URL}/learning-objectives", json=payload)
    assert r.status_code == 200, r.text
    print("✓ POST /learning-objectives passed")

    print("\n── GET /learning-objectives ──")
    r = requests.get(f"{BASE_URL}/learning-objectives")
    assert r.status_code == 200, r.text
    assert "science101" in r.json(), "science101 missing from learning objectives"
    print("✓ GET /learning-objectives passed")


def test_create_student():
    print("\n── POST /create-student ──")
    payload = {"user_id": "student1", "lesson_id": "science101"}
    r = requests.post(f"{BASE_URL}/create-student", json=payload)
    assert r.status_code == 200, r.text
    print("✓ POST /create-student passed")


def test_get_students():
    print("\n── GET /get-students ──")
    r = requests.get(f"{BASE_URL}/get-students")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "student1" in data["students"], "student1 missing from students list"
    print("✓ GET /get-students passed:", data)


def test_get_roster():
    print("\n── GET /get-roster/science101 ──")
    r = requests.get(f"{BASE_URL}/get-roster/science101")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "student1" in data["roster"], "student1 missing from roster"
    print("✓ GET /get-roster passed:", data)


async def test_websocket_conversation():
    """Send a few messages and verify the teacher responds each time."""
    uri = f"{BASE_WS_URL}/student1"
    print(f"\n── WebSocket conversation at {uri} ──")

    messages = [
        "Hi, I'm ready to learn!",
        "How many planets are in the solar system?",
        "What is the largest planet?",
    ]
    i = 0
    async with websockets.connect(uri) as ws:
        for msg in messages:
            print(f"  → Sending: {msg}")
            await ws.send(msg)
            response = await ws.recv()
            print(f"  ← Teacher: {response[:120]}{'...' if len(response) > 120 else ''}")
            assert response, "Empty response from teacher"

    print("✓ WebSocket conversation passed")


async def test_convo():
    """Send a few messages and verify the teacher responds each time."""
    uri = f"{BASE_WS_URL}/student1"
    print(f"\n── WebSocket conversation at {uri} ──")

    messages = [
        "Hi, I'm ready to learn!",
        "How many planets are in the solar system?",
        "What is the largest planet?",
    ]
    i = 0
    async with websockets.connect(uri) as ws:
        while i < 7:
            msg = input()
            await ws.send(msg)
            response = await ws.recv()
            print(f"  ← Teacher: {response[:120]}{'...' if len(response) > 120 else ''}")
            assert response, "Empty response from teacher"
            i+=1
    print("✓ WebSocket conversation passed")

def test_get_performance():
    print("\n── GET /performance/student1 ──")
    r = requests.get(f"{BASE_URL}/performance/student1")
    if r.status_code == 404:
        print("No performance data yet (run more chat turns first)")
    else:
        assert r.status_code == 200, r.text
        data = r.json()
        print("  Assessment:", data.get("assessment"))
        print("  Mastered:", data.get("mastered"))
        print("✓ GET /performance passed")


if __name__ == "__main__":
    test_learning_objectives()
    test_create_student()
    test_get_students()
    test_get_roster()
   # asyncio.run(test_websocket_conversation())
    test_get_performance()
    print("\n✓ All tests done.")
    asyncio.run(test_convo())
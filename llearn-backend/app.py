from flask import Flask, request, jsonify
from data import learning_objectives_store,active_assessors,active_students
import Assessor
import Student

# Declare the dict type
app = Flask(__name__)

# In-memory storage for demo purposes

json_error = {"error": "Request must be JSON"}
@app.route('/api/learning-objectives', methods=['POST'])
def add_learning_objectives():
    if not request.is_json:
        return jsonify(json_error), 400
    
    data = request.get_json()

    # Expecting JSON like:
    # {
    #   "lesson_id": "science101",
    #   "title": "Introduction to plants",
    #   "objectives": [
    #       {"id": "obj1", "text": "Understand the number of planets"},
    #       {"id": "obj2", "text": "Know the largest planet"}
    #    ]
    # }

    required_fields = ["lesson_id", "title", "objectives"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field '{field}'"}), 400

    if not isinstance(data["objectives"], list):
        return jsonify({"error": "'objectives' must be a list"}), 400

    for obj in data["objectives"]:
        if not isinstance(obj, str):
            return jsonify({"error": "Each objective must be a string"}), 400

    lesson_id = data["lesson_id"]
    # Update or add the lesson entry
    learning_objectives_store[lesson_id] = {
        "title": data["title"],
        "objectives": data["objectives"]
    }

    return jsonify({
        "message": f"Learning objectives for lesson '{lesson_id}' received",
        "count": len(data["objectives"])
    }), 200

@app.route('/api/learning-objectives', methods=['GET'])
def get_learning_objectives():
    return jsonify(learning_objectives_store), 200


@app.route('/api/create-student', methods=['POST'])
def create_student():
    if not request.is_json:
        return jsonify(json_error), 400
    
    data = request.get_json()
    required_fields = ["user_id", "lesson_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field '{field}'"}), 400  

  
    active_students[data['user_id']]=(Student.StudentChat(user_id=data['user_id'], lesson_id= data['lesson_id']))
    return jsonify({"message": f"Student {data['user_id']} created"}), 200



@app.route('/api/create-assessor', methods=['POST'])
def create_assessor():
    if not request.is_json:
        return jsonify(json_error), 400
    
    data = request.get_json()
    required_fields = ["class_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field '{field}'"}), 400  
    class_id = data['class_id']
    objectives= learning_objectives_store[class_id]
    active_assessors[class_id]=(Assessor.AssessorChat(objectives=objectives,class_id=class_id))
    return jsonify({"message": f"Asessor for {class_id} created"}), 200


@app.route('/api/performance/<user_id>', methods=['GET'])
def get_performance(user_id):
    print(active_students)
    if user_id not in active_students:
        return jsonify({"error": "Student not found"}), 404
    student = active_students[user_id]
    assessor = active_assessors[student.lesson_id]
    logs=assessor.session_logs
    print(logs)
    most_recent_score={}
    for score in reversed(logs):
        if score['user_id'] == user_id:
            most_recent_score = score
            break

    return jsonify(most_recent_score)


@app.route('/api/submit_chat/<user_id>', methods=['POST'])
def submit_chat(user_id):
    if not request.is_json:
        return jsonify(json_error), 400
    
    data = request.get_json()
    required_fields = ["message"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field '{field}'"}), 400  
        

    student = active_students[user_id]
    response= student.send_new_message(data['message'])
    return jsonify({"response": response}), 200


@app.route('/api/assess_performance/<user_id>', methods=['GET'])
def assess_performance(user_id):
 

    student = active_students[user_id]
    assessor = active_assessors[student.lesson_id]
    chat_history = student.chat_history
    response= assessor.assess_performance(chat_history=chat_history,student_id= student.user_id)
    return jsonify({"response": response}), 200

if __name__ == '__main__':
    app.run(debug=True)
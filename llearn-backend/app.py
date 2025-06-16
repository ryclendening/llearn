from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage for demo purposes
learning_objectives_store = {
  "science101": {
    "title": "Introduction to plants",
    "objectives": [
      "Understand the number of planet's in the solar system",
      "Know the largest planet",
      "Know the smallest planet",
      "Demonstrate understanding of an orbit"
    ]
  }
}

@app.route('/api/learning-objectives', methods=['POST'])
def add_learning_objectives():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
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

if __name__ == '__main__':
    app.run(debug=True)
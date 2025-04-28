from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    keywords = data.get("keywords", [])
    slides_path = "all_slides.jsonl"
    videos_path = "all_videos.jsonl"

    slide_matches = []
    video_matches = []

    def score_content(fields, weights, keywords):
        score = 0
        for keyword in keywords:
            keyword = keyword.lower()
            for field, weight in zip(fields, weights):
                if keyword in field.lower():
                    score += weight
        return score

    with open(slides_path, 'r', encoding='utf-8') as f:
        for line in f:
            slide = json.loads(line)
            score = score_content([slide.get("slide_text", ""), slide.get("presenter_notes", "")], [1, 2], keywords)
            if score > 0:
                slide["score"] = score
                slide_matches.append(slide)

    with open(videos_path, 'r', encoding='utf-8') as f:
        for line in f:
            video = json.loads(line)
            score = score_content([video.get("transcript", "")], [2], keywords)
            if score > 0:
                video["score"] = score
                video_matches.append(video)

    return jsonify({
        "slide_matches": sorted(slide_matches, key=lambda x: x["score"], reverse=True),
        "video_matches": sorted(video_matches, key=lambda x: x["score"], reverse=True)
    })


@app.route('/get_question', methods=['POST'])
def get_question():
    data = request.get_json()
    assignment = data.get("assignment")
    question_number = data.get("question_number")

    try:
        requested_q = int(question_number)
    except:
        return jsonify({{"error": "Invalid question number format"}}), 400

    with open("all_assignments.jsonl", "r") as f:
        questions = [json.loads(line) for line in f]

    filtered = [q for q in questions if q.get("assignment") == assignment]

    for q in filtered:
        q_num = q.get("question_number")
        if "-" in q_num:
            start, end = map(int, q_num.split("-"))
            if start <= requested_q <= end:
                q["requested_sub_question"] = requested_q
                if q.get("type") == "matching":
                    sub_index = requested_q - start
                    if sub_index < len(q["matches"]):
                        q["highlighted_pair"] = q["matches"][sub_index]
                return jsonify(q)
        else:
            if int(q_num) == requested_q:
                return jsonify(q)

    return jsonify({"error": "Question not found"}), 404

@app.route("/lookup_key", methods=["POST"])
def lookup_key():
    data = request.get_json()
    lookup_type = data.get("lookup_type")
    lookup_value = data.get("lookup_value")

    if not lookup_type or not lookup_value:
        return jsonify({"error": "lookup_type and lookup_value are required"}), 400

    lookup_value = lookup_value.lower().strip()

    matches = []
    
    with open("Lecture_Review_Exam_Key.jsonl", "r") as f:
      key_data = [json.loads(line) for line in f]

    for entry in key_data:
        if lookup_type == "lecture":
            for lecture in entry.get("lectures", []):
                if lookup_value == lecture.lower():
                    matches.append(entry)
        elif lookup_type == "review":
            if lookup_value == entry.get("review", "").lower():
                matches.append(entry)
        elif lookup_type == "midterm":
            if lookup_value == entry.get("exam", "").lower():
                matches.append(entry)

    if not matches:
        return jsonify({"error": "No matching data found."}), 404

    return jsonify({"matches": matches})
    
@app.route("/get_lecture", methods=["POST"])
def get_lecture():
    data = request.get_json()
    lecture = data.get("lecture")  # Expects single lecture like "Lecture3"

    if not lecture:
        return jsonify({"error": "lecture is required."}), 400

    try:
        # Load your slides database
        with open("all_slides.jsonl", "r") as f:
            slides_data = [json.loads(line) for line in f]
    except FileNotFoundError:
        return jsonify({"error": "Slides database not found."}), 500

    matches = [slide for slide in slides_data if slide.get("lecture", "").lower() == lecture.lower()]

    if not matches:
        return jsonify({"error": f"No slides found for {lecture}."}), 404

    return jsonify({"slides": matches})

if __name__ == "__main__":
    import logging
    log = logging.getLogger('werkzeug')
    # log.setLevel(logging.ERROR)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
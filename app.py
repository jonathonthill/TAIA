from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

@app.route("/search", methods=["POST"])
def search():
    data = request.json
    keywords = data.get("keywords", [])
    slides_path = "all_slides.jsonl"
    videos_path = "all_videos.jsonl"

    slide_matches = []
    video_matches = []

    # Score helper
    def score_content(fields, weights, keywords):
        score = 0
        content = " ".join(fields).lower()
        for keyword in keywords:
            keyword = keyword.lower()
            for field, weight in zip(fields, weights):
                if keyword in field.lower():
                    score += weight
        return score

    # Search slides
    with open(slides_path, 'r', encoding='utf-8') as f:
        for line in f:
            slide = json.loads(line)
            fields = [
                slide.get("slide_title", ""),
                slide.get("presenter_notes", ""),
                slide.get("slide_text", "")
            ]
            weights = [3, 2, 1]
            score = score_content(fields, weights, keywords)
            if score > 0:
                slide_matches.append({
                    "Lecture": slide["lecture"],
                    "Slide": slide["slide_number"],
                    "Title": slide.get("slide_title"),
                    "Score": score
                })

    # Collapse to ranges per lecture
    from collections import defaultdict

    grouped_slides = defaultdict(list)
    for match in slide_matches:
        grouped_slides[match["Lecture"]].append(match["Slide"])

    slide_results = []
    for lecture, slides in grouped_slides.items():
        slide_results.append({
            "Lecture": lecture,
            "SlideRange": [min(slides), max(slides)]
        })

    # Search videos
    with open(videos_path, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            fields = [
                entry.get("title", ""),
                entry.get("keywords", ""),
                entry.get("transcript", "")
            ]
            weights = [3, 2, 1]
            score = score_content(fields, weights, keywords)
            if score > 0:
                video_matches.append({
                    "Title": entry.get("title"),
                    "URL": entry.get("url"),
                    "Score": score
                })

    video_matches.sort(key=lambda x: -x["Score"])

    return jsonify({
        "SlideMatches": slide_results,
        "VideoMatches": video_matches[:3]  # top 3
    })

@app.route("/get_question", methods=["POST"])
def get_question():
    data = request.json
    question_number = data.get("question_number")
    assignment = data.get("assignment")
    assignment_file = "all_assignments.jsonl"

    if not question_number or not assignment:
        return jsonify({"error": "Missing question_number or assignment"}), 400

    results = []

    with open(assignment_file, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            if (
                entry.get("question_number") == question_number
                and entry.get("assignment", "").lower() == assignment.lower()
            ):
                results.append(entry)

    if not results:
        return jsonify({
            "error": f"No match for assignment: {assignment}, question_number: {question_number}"
        }), 404

    return jsonify({"matches": results})
if __name__ == "__main__":
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

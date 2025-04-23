from flask import Flask, request, jsonify
import json
import os
from collections import defaultdict

app = Flask(__name__)

@app.route("/search", methods=["POST"])
def search():
    data = request.json
    keywords = data.get("keywords", [])
    slides_path = "all_slides.jsonl"
    videos_path = "YouTube_Transcript_Index_With_Text.jsonl"

    slide_matches = defaultdict(list)
    video_matches = []

    # Search slides
    with open(slides_path, 'r', encoding='utf-8') as f:
        for line in f:
            slide = json.loads(line)
            lecture = slide["lecture"]
            slide_num = slide["slide_number"]
            content = f'{slide.get("slide_title", "")} {slide.get("slide_text", "")} {slide.get("presenter_notes", "")}'.lower()
            if any(keyword.lower() in content for keyword in keywords):
                slide_matches[lecture].append(slide_num)

    slide_results = []
    for lecture, slides in slide_matches.items():
        slide_results.append({
            "Lecture": lecture,
            "SlideRange": [min(slides), max(slides)]
        })

    # Search video transcripts
    with open(videos_path, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            content = f'{entry.get("title", "")} {entry.get("transcript", "")} {entry.get("keywords", "")}'.lower()
            if any(keyword.lower() in content for keyword in keywords):
                video_matches.append({
                    "Title": entry.get("title"),
                    "URL": entry.get("url")
                })

    return jsonify({
        "SlideMatches": slide_results,
        "VideoMatches": video_matches
    })
    
@app.route("/get_question", methods=["POST"])
def get_question():
    data = request.json
    question_number = data.get("question_number")
    assignment = data.get("assignment")
    assignment_file = "all_reviews_parsed.jsonl"

    if not question_number or not assignment:
        return jsonify({"error": "Missing question_number or assignment"}), 400

    results = []

    with open(assignment_file, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            if (
                entry.get("question_number") == question_number
                and entry.get("topic", "").lower() == assignment.lower()
            ):
                results.append(entry)

    if not results:
        return jsonify({
            "error": f"No match for assignment: {assignment}, question_number: {question_number}"
        }), 404

    return jsonify({"matches": results})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # default for local testing
    app.run(host="0.0.0.0", port=port, debug=False)

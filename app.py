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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # default for local testing
    app.run(host="0.0.0.0", port=port, debug=False)

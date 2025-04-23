from flask import Flask, request, jsonify
import json
from collections import defaultdict

app = Flask(__name__)

@app.route("/search", methods=["POST"])
def search_slides():
    data = request.json
    keywords = data.get("keywords", [])
    file_path = data.get("file_path", "all_slides.jsonl")

    matches = defaultdict(list)
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            slide = json.loads(line)
            lecture = slide["lecture"]
            slide_num = slide["slide_number"]
            content = f'{slide["slide_title"]} {slide["full_text"]}'.lower()
            if any(keyword.lower() in content for keyword in keywords):
                matches[lecture].append(slide_num)

    results = []
    for lecture, slides in matches.items():
        results.append({
            "Lecture": lecture,
            "SlideRange": [min(slides), max(slides)]
        })

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)

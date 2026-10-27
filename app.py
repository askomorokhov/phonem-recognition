"""Web demo: picture cards + microphone -> word / sounds / letters check.

    python app.py      # then open http://localhost:8000
"""
from flask import Flask, abort, jsonify, request, send_from_directory

from recognition import check_word
from recognition.checker import ENGINES
from words import LANGUAGES, WORDS

app = Flask(__name__, static_folder="static")
app.json.sort_keys = False  # keep language order from words.py


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/api/words")
def words():
    return jsonify({"languages": LANGUAGES, "words": WORDS})


@app.post("/api/check")
def check():
    """Body: raw 16 kHz mono 16-bit little-endian PCM.
    Query: ?lang=en&word=apple&engines=word,phonemes,spelling (engines optional, default all)"""
    lang = request.args.get("lang")
    card = next((w for w in WORDS if w["id"] == request.args.get("word")), None)
    engines = request.args.get("engines", ",".join(ENGINES)).split(",")
    if lang not in LANGUAGES or card is None:
        abort(400, "unknown lang or word")
    if not set(engines) & set(ENGINES):
        abort(400, f"engines must include at least one of {ENGINES}")
    return jsonify(check_word(lang, card[lang], request.get_data(), engines))


if __name__ == "__main__":
    app.run(debug=True, port=8000)

from flask import Flask, render_template, redirect, url_for, session, request
import json
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "nyc-neighborhoods-secret"

with open("data.json") as f:
    DATA = json.load(f)

ZONES = DATA["zones"]
NUM_ZONES = len(ZONES)
QUESTIONS = DATA["quiz_questions"]
NUM_QUESTIONS = len(QUESTIONS)

HOOD_TO_ZONE = {
    hood["name"]: zone
    for zone in ZONES
    for hood in zone["neighborhoods"]
}

HOOD_FACTS = {
    hood["name"]: hood["fact"]
    for zone in ZONES
    for hood in zone["neighborhoods"]
}


@app.route("/")
def home():
    session.clear()
    return render_template("home.html")


@app.route("/start", methods=["POST"])
def start():
    session.clear()
    session["started_at"] = datetime.utcnow().isoformat()
    return redirect(url_for("learn"))


@app.route("/learn")
def learn():
    start_zone = max(1, min(NUM_ZONES, request.args.get("zone", 1, type=int)))
    from_quiz = request.args.get("from") == "quiz"
    return render_template("learn.html", zones=ZONES, num_zones=NUM_ZONES,
                           start_zone=start_zone, from_quiz=from_quiz)


def _get_quiz_order():
    if "quiz_order" not in session:
        order = list(range(NUM_QUESTIONS))
        random.shuffle(order)
        session["quiz_order"] = order
    return session["quiz_order"]


@app.route("/quiz/restart")
def quiz_restart():
    session.pop("quiz_order", None)
    session.pop("quiz_answers", None)
    session.pop("quiz_attempts", None)
    return redirect(url_for("quiz"))


@app.route("/quiz")
def quiz():
    order = _get_quiz_order()
    questions = [QUESTIONS[i]["find"] for i in order]
    question_zones = [HOOD_TO_ZONE.get(QUESTIONS[i]["find"], {}).get("number", 1) for i in order]
    quiz_answers = session.get("quiz_answers", {})
    correct_names = [questions[int(k)] for k in quiz_answers]
    starting_q = len(quiz_answers)
    return render_template("quiz.html",
                           questions=questions,
                           question_zones=question_zones,
                           num_questions=NUM_QUESTIONS,
                           correct_names=correct_names,
                           starting_q=starting_q)


@app.route("/quiz/check", methods=["POST"])
def quiz_check():
    order = _get_quiz_order()
    data = request.get_json()
    q_index = int(data.get("q_index", 0))
    answer = data.get("answer", "")

    if q_index < 0 or q_index >= NUM_QUESTIONS:
        return {"error": "invalid"}, 400

    correct = answer == QUESTIONS[order[q_index]]["find"]

    if correct:
        quiz_answers = session.get("quiz_answers", {})
        quiz_answers[str(q_index)] = answer
        session["quiz_answers"] = quiz_answers
        session.modified = True
    else:
        attempts = session.get("quiz_attempts", {})
        key = str(q_index)
        attempts[key] = attempts.get(key, 0) + 1
        session["quiz_attempts"] = attempts
        session.modified = True

    return {"correct": correct}


@app.route("/quiz/hint", methods=["POST"])
def quiz_hint():
    data = request.get_json()
    q_index = int(data.get("q_index", 0))
    if q_index < 0 or q_index >= NUM_QUESTIONS:
        return {"error": "invalid"}, 400
    attempts = session.get("quiz_attempts", {})
    key = str(q_index)
    attempts[key] = attempts.get(key, 0) + 1
    session["quiz_attempts"] = attempts
    session.modified = True
    return {"ok": True}


@app.route("/results")
def results():
    order = session.get("quiz_order", list(range(NUM_QUESTIONS)))
    quiz_answers = session.get("quiz_answers", {})
    attempts = session.get("quiz_attempts", {})
    score = 0
    results_data = []
    for i in range(NUM_QUESTIONS):
        q = QUESTIONS[order[i]]
        answered = str(i) in quiz_answers
        wrong_count = attempts.get(str(i), 0)
        if answered and wrong_count == 0:
            score += 2
        elif answered:
            score += 1
        z = HOOD_TO_ZONE.get(q["find"], {})
        results_data.append({
            "target": q["find"],
            "correct": answered,
            "tries": wrong_count + (1 if answered else 0),
            "zone_num": z.get("number", 0),
            "zone_name": z.get("name", ""),
            "zone_color": z.get("color", "#ccc"),
            "fact": HOOD_FACTS.get(q["find"], ""),
        })
    max_score = NUM_QUESTIONS * 2
    return render_template("results.html", results=results_data, score=score,
                           max_score=max_score, num_questions=NUM_QUESTIONS)


if __name__ == "__main__":
    app.run(debug=True, port=5001)

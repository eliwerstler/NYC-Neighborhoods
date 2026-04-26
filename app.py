from flask import Flask, render_template, redirect, url_for, session, request
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "nyc-neighborhoods-secret"

with open("data.json") as f:
    DATA = json.load(f)

ZONES = DATA["zones"]
NUM_ZONES = len(ZONES)
QUESTIONS = DATA["quiz_questions"]
NUM_QUESTIONS = len(QUESTIONS)


@app.route("/")
def home():
    session.clear()
    return render_template("home.html")


@app.route("/start", methods=["POST"])
def start():
    session.clear()
    session["started_at"] = datetime.utcnow().isoformat()
    session["learn_times"] = {}
    return redirect(url_for("learn", zone_num=1))


@app.route("/learn/<int:zone_num>")
def learn(zone_num):
    if zone_num < 1 or zone_num > NUM_ZONES:
        return redirect(url_for("home"))

    learn_times = session.get("learn_times", {})
    learn_times[str(zone_num)] = datetime.utcnow().isoformat()
    session["learn_times"] = learn_times

    zone = ZONES[zone_num - 1]
    is_last = zone_num == NUM_ZONES
    return render_template("learn.html", zone=zone, zone_num=zone_num,
                           num_zones=NUM_ZONES, is_last=is_last)


@app.route("/quiz/<int:q_num>", methods=["GET", "POST"])
def quiz(q_num):
    if q_num < 1 or q_num > NUM_QUESTIONS:
        return redirect(url_for("home"))

    if request.method == "POST":
        answer = request.form.get("answer", "")
        quiz_answers = session.get("quiz_answers", {})
        quiz_answers[str(q_num)] = answer
        session["quiz_answers"] = quiz_answers

        if q_num == NUM_QUESTIONS:
            return redirect(url_for("results"))
        return redirect(url_for("quiz", q_num=q_num + 1))

    question = QUESTIONS[q_num - 1]
    return render_template("quiz.html", question=question, q_num=q_num,
                           num_questions=NUM_QUESTIONS)


@app.route("/results")
def results():
    quiz_answers = session.get("quiz_answers", {})
    score = 0
    results_data = []
    for i, q in enumerate(QUESTIONS, 1):
        user_answer = quiz_answers.get(str(i), "")
        correct = user_answer == q["find"]
        if correct:
            score += 1
        results_data.append({
            "target": q["find"],
            "user_answer": user_answer or "No answer",
            "correct": correct,
        })
    return render_template("results.html", results=results_data, score=score,
                           num_questions=NUM_QUESTIONS)


if __name__ == "__main__":
    app.run(debug=True, port=5001)

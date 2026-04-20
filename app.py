from flask import Flask, render_template, redirect, url_for, session
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "nyc-neighborhoods-secret"

with open("data.json") as f:
    DATA = json.load(f)

ZONES = DATA["zones"]
NUM_ZONES = len(ZONES)


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


# Stubs for partner to implement
@app.route("/quiz/<int:q_num>")
def quiz(q_num):
    return f"<h1>Quiz question {q_num} — coming soon</h1>"


@app.route("/results")
def results():
    return "<h1>Results — coming soon</h1>"


if __name__ == "__main__":
    app.run(debug=True)

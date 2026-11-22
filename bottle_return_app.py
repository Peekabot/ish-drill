#!/usr/bin/env python3
"""
Minimal bottle-return logger for PythonAnywhere
POST /log  {"amount": 7.50, "note": "optional"}
GET  /     shows recent entries
"""
from flask import Flask, request, jsonify, render_template_string
import json
import os
from datetime import datetime

app = Flask(__name__)
LOG_FILE = os.path.join(os.path.dirname(__file__), "bottle_log.json")

def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE) as f:
            return json.load(f)
    except Exception:
        return []

def save_log(entries):
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)

@app.route("/")
def index():
    entries = load_log()[-20:]
    total = sum(e.get("amount", 0) for e in load_log())
    html = """
    <h2>Bottle Return Log</h2>
    <p>Total logged: ${{ "%.2f"|format(total) }}</p>
    <ul>
    {% for e in entries %}
      <li>{{ e.timestamp }} — ${{ "%.2f"|format(e.amount) }} {% if e.note %}({{ e.note }}){% endif %}</li>
    {% endfor %}
    </ul>
    <form method="post" action="/log">
      Amount: <input name="amount" type="number" step="0.01" required><br>
      Note: <input name="note"><br>
      <button>Log</button>
    </form>
    """
    return render_template_string(html, entries=entries, total=total)

@app.route("/log", methods=["POST"])
def log():
    data = request.get_json(silent=True) or request.form
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "bad amount"}), 400
    note = (data.get("note") or "").strip()
    entries = load_log()
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "amount": amount,
        "note": note
    }
    entries.append(entry)
    save_log(entries)
    return jsonify({"ok": True, "entry": entry})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from pathlib import Path
import json

app = Flask(__name__)
CORS(app)

BASE = Path.home() / "Masaüstü" / "theia-guard-core"
LOG = BASE / "theia_guard_log.json"
APPROVAL = BASE / "pending_approval.json"
DASHBOARD = Path.home() / "Masaüstü" / "theia-guard" / "dashboard.html"

def read_json(path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            return []
    return []

@app.route("/")
def index():
    return send_file(DASHBOARD)

@app.route("/api/stats")
def stats():
    entries = read_json(LOG)
    return jsonify({
        "total": len(entries),
        "auto": sum(1 for e in entries if e.get("decision") == "auto_approved"),
        "approved": sum(1 for e in entries if "approved" in e.get("decision","") and e.get("decision") != "auto_approved"),
        "denied": sum(1 for e in entries if "denied" in e.get("decision","")),
        "blocked": sum(1 for e in entries if e.get("decision") == "blocked"),
    })

@app.route("/api/logs")
def logs():
    entries = read_json(LOG)
    return jsonify(list(reversed(entries[-50:])))

@app.route("/api/pending")
def pending():
    data = read_json(APPROVAL)
    if isinstance(data, dict) and data.get("status") == "pending":
        return jsonify(data)
    return jsonify(None)

@app.route("/api/approve", methods=["POST"])
def approve():
    if APPROVAL.exists():
        data = json.loads(APPROVAL.read_text())
        data["status"] = "approved"
        APPROVAL.write_text(json.dumps(data))
        return jsonify({"ok": True})
    return jsonify({"ok": False})

@app.route("/api/deny", methods=["POST"])
def deny():
    if APPROVAL.exists():
        data = json.loads(APPROVAL.read_text())
        data["status"] = "denied"
        APPROVAL.write_text(json.dumps(data))
        return jsonify({"ok": True})
    return jsonify({"ok": False})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

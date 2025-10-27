from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/telemetry")
def telemetry():
    return jsonify({
        "sniffer": "all clear on local ports",
        "hopper": "port hop stable / cloak engaged",
        "healer": "shield green / bubble field intact",
        "maya": "awake and watching you 💖"
    })


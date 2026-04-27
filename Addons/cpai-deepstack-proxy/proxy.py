import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
CPAI_URL = os.environ.get("CPAI_URL", "http://192.168.4.10:32168")


def forward_image(endpoint):
    files = {}
    if "image" in request.files:
        f = request.files["image"]
        files["image"] = (f.filename, f.stream, f.mimetype)
    data = {k: v for k, v in request.form.items() if k != "image"}
    return requests.post(f"{CPAI_URL}{endpoint}", files=files, data=data, timeout=30)


@app.route("/v1/vision/face/recognize", methods=["POST"])
def recognize():
    try:
        r = forward_image("/v1/vision/face/recognize")
        cp = r.json()
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "predictions": []}), 200

    predictions = []
    for face in cp.get("predictions", []):
        predictions.append({
            "userid": face.get("userid", "unknown"),
            "confidence": face.get("confidence", 0),
            "y_min": face.get("y_min", 0),
            "x_min": face.get("x_min", 0),
            "y_max": face.get("y_max", 0),
            "x_max": face.get("x_max", 0),
        })

    return jsonify({
        "success": cp.get("success", False),
        "predictions": predictions,
        "error": cp.get("error"),
    })


@app.route("/v1/vision/face/register", methods=["POST"])
def register():
    userid = request.form.get("userid", "")
    try:
        r = forward_image("/v1/vision/face/register")
        cp = r.json()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 200

    return jsonify({
        "success": cp.get("success", False),
        "message": f"Face registered for {userid}" if cp.get("success") else cp.get("error", "Failed"),
    })


@app.route("/v1/vision/face/delete", methods=["POST"])
def delete():
    userid = request.form.get("userid", "")
    try:
        r = requests.post(f"{CPAI_URL}/v1/vision/face/delete", data={"userid": userid}, timeout=10)
        cp = r.json()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 200

    return jsonify({"success": cp.get("success", False)})


@app.route("/v1/vision/face/list", methods=["POST"])
def list_faces():
    try:
        r = requests.post(f"{CPAI_URL}/v1/vision/face/list", timeout=10)
        cp = r.json()
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "faces": []}), 200

    return jsonify({
        "success": cp.get("success", False),
        "faces": cp.get("faces", []),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

"""
Jarvis Conversation Agent Server
Exposes Jarvis as an HTTP API for Home Assistant integration.
"""
from flask import Flask, request, jsonify
from llm import Brain
import config
import os

app = Flask(__name__)

# Initialize Jarvis Brain
print("Initializing J.A.R.V.I.S Brain...")
brain = Brain()
print("J.A.R.V.I.S Ready.")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "agent": "jarvis"})

@app.route('/conversation', methods=['POST'])
def conversation():
    """
    Main conversation endpoint.
    Expects JSON: {"text": "user input"}
    Returns JSON: {"response": "jarvis response"}
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' in request body"}), 400
        
        user_input = data['text']
        print(f"[Jarvis] Received: {user_input}")
        
        response = brain.process(user_input)
        print(f"[Jarvis] Response: {response}")
        
        return jsonify({"response": response})
    except Exception as e:
        print(f"[Jarvis] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/intent', methods=['POST'])
def intent():
    """
    Intent handler for HA conversation integration.
    Matches format expected by custom conversation agents.
    """
    try:
        data = request.get_json()
        # HA sends different formats, handle both
        text = data.get('text') or data.get('speech', {}).get('plain', {}).get('speech', '')
        
        if not text:
            return jsonify({"error": "No text found in request"}), 400
        
        response = brain.process(text)
        
        # Return in HA conversation format
        return jsonify({
            "speech": {
                "plain": {
                    "speech": response
                }
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('JARVIS_PORT', 5000))
    print(f"Starting Jarvis server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)

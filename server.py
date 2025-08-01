from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# Change this path to match your system if needed
MT5_SIGNAL_FILE = os.path.expanduser("~") + "/AppData/Roaming/MetaQuotes/Terminal/Common/Files/signal.txt"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    if not data or 'action' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid payload'}), 400

    try:
        with open(MT5_SIGNAL_FILE, "w") as f:
            json.dump(data, f)
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

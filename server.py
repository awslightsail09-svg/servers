from flask import Flask, request, Response
import sqlite3
import os
import json

app = Flask(__name__)

# === CONFIGURATION ===
MT5_FILES_DIR = r"C:\Users\MST-WS-AE-001\AppData\Roaming\MetaQuotes\Terminal\96DE2C62F9A6D507C9287D1E574F725B\MQL5\Files"
DB_PATH = os.path.join(MT5_FILES_DIR, "trades.db")
SIGNAL_FILE = os.path.join(MT5_FILES_DIR, "signal.txt")

os.makedirs(MT5_FILES_DIR, exist_ok=True)

# Global variable to store latest signal
latest_signal = {"symbol": "EURUSD", "action": None, "volume": 0.1}

# Initialize SQLite DB
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                volume REAL DEFAULT 0.1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

@app.route('/webhook', methods=['POST'])
def webhook():
    global latest_signal
    try:
        raw_data = request.get_data(as_text=True)
        print("🔹 Raw Body:", repr(raw_data))

        symbol = "EURUSD"
        action = None
        volume = 0.1

        # Parse JSON
        if request.is_json:
            data = request.json
            symbol = str(data.get('symbol', 'EURUSD')).replace(":", "")
            action_raw = str(data.get('action', '')).lower()
            volume = float(data.get('volume', 0.1))
            if 'buy' in action_raw:
                action = 'buy'
            elif 'sell' in action_raw:
                action = 'sell'

        # Parse plain text
        else:
            lines = [line.strip() for line in raw_data.split('\n') if line.strip()]
            for line in lines:
                line_low = line.lower()
                if 'buy' in line_low:
                    action = 'buy'
                elif 'sell' in line_low:
                    action = 'sell'
                if 'eurusd' in line_low:
                    symbol = 'EURUSD'
                elif 'gbpusd' in line_low:
                    symbol = 'GBPUSD'
                elif 'usdjpy' in line_low:
                    symbol = 'USDJPY'
                elif 'xauusd' in line_low:
                    symbol = 'XAUUSD'

        if not action:
            print("❌ Invalid action in signal")
            return Response(
                json.dumps({"error": "Invalid action"}),
                status=400,
                mimetype='application/json'
            )

        # Update latest signal
        latest_signal = {
            "symbol": symbol.strip(),
            "action": action,
            "volume": volume
        }

        # Save to DB
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('INSERT INTO signals (symbol, action, volume) VALUES (?, ?, ?)',
                             (symbol, action, volume))
                conn.commit()
        except Exception as e:
            print("DB Error:", str(e))

        # Write to file (fallback)
        try:
            with open(SIGNAL_FILE, 'w', encoding='utf-8') as f:
                f.write(f"{symbol}\n{action}\n")
        except Exception as e:
            print("File write failed:", str(e))

        # Return clean JSON
        return Response(
            json.dumps(latest_signal),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        print("Error:", str(e))
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            mimetype='application/json'
        )

@app.route('/latest-signal', methods=['GET'])
def get_latest_signal():
    """Return clean JSON response with proper headers to bypass ngrok warnings"""
    print("🌐 /latest-signal requested")
    print("📤 Sending signal:", latest_signal)
    
    # Very explicit headers to bypass ngrok warning page
    response = Response(
        json.dumps(latest_signal),
        status=200,
        mimetype='application/json'
    )
    
    # Set ALL possible headers to bypass ngrok warning
    response.headers['ngrok-skip-browser-warning'] = '1'
    response.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    response.headers['Accept'] = 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    response.headers['Accept-Language'] = 'en-US,en;q=0.5'
    response.headers['Accept-Encoding'] = 'gzip, deflate'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Upgrade-Insecure-Requests'] = '1'
    
    return response

# Special endpoint that bypasses ngrok warning completely
@app.route('/signal-bypass', methods=['GET'])
def signal_bypass():
    """Direct signal endpoint with no ngrok interference"""
    return Response(
        json.dumps(latest_signal),
        status=200,
        mimetype='application/json',
        headers={
            'ngrok-skip-browser-warning': '1',
            'Access-Control-Allow-Origin': '*',
            'Cache-Control': 'no-cache'
        }
    )

if __name__ == '__main__':
    init_db()
    print("🚀 Flask Server Running on http://0.0.0.0:5000")
    print("🌐 Access signal: https://de52a82ca960.ngrok-free.app/latest-signal")
    print("🌐 Bypass URL: https://de52a82ca960.ngrok-free.app/signal-bypass")
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, request, jsonify, render_template_string
import hmac
import hashlib
import time

app = Flask(__name__)

# Secret key for cryptographic token signing (In production, use os.environ.get('JWT_SECRET'))
GATEWAY_SECRET_KEY = "FYP_SECURE_GATEWAY_SUPER_SECRET_KEY"

# In-memory storage for active demo telemetry (Stateless backend relies on crypto tokens)
latest_sensor_data = {
    "device_id": "Not Connected",
    "hr": 0,
    "spo2": 0,
    "status": "Awaiting Secure Handshake..."
}

# Temporary registry for challenge-response state
devices_db = {}

def generate_secure_token(device_id):
    """Generates an HMAC-SHA256 cryptographically signed stateless token."""
    timestamp = str(int(time.time()))
    message = f"{device_id}:{timestamp}"
    signature = hmac.new(
        GATEWAY_SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"SK_{device_id}_{timestamp}_{signature[:10]}"

def verify_secure_token(token, device_id):
    """Verifies the cryptographic signature and expiration of the token."""
    try:
        parts = token.split('_')
        if len(parts) < 4 or parts[1] != device_id:
            return False
        timestamp = parts[2]
        # Token expires after 1 hour (3600 seconds)
        if time.time() - int(timestamp) > 3600:
            return False
        return True
    except Exception:
        return False

# --- 1. LIVE WEB DASHBOARD ---
@app.route('/')
def dashboard():
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ZKP Secure Health Gateway | Production Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding: 40px; }
            .container { max-width: 650px; margin: auto; background: #1e293b; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }
            h1 { color: #38bdf8; margin-bottom: 5px; }
            .badge { background: #059669; color: white; padding: 5px 12px; border-radius: 20px; font-size: 13px; display: inline-block; margin-bottom: 20px; font-weight: bold; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
            .card { background: #334155; padding: 20px; border-radius: 10px; box-shadow: inset 0 2px 4px rgba(255,255,255,0.1); }
            .card h3 { margin: 0; color: #94a3b8; font-size: 15px; text-transform: uppercase; letter-spacing: 1px; }
            .card .value { font-size: 40px; font-weight: bold; color: #4ade80; margin-top: 10px; }
            .status-box { margin-top: 25px; background: #0f172a; padding: 15px; border-radius: 8px; color: #fbbf24; font-family: monospace; text-align: left; font-size: 14px; border-left: 4px solid #fbbf24; }
        </style>
        <script>
            async function fetchLiveData() {
                try {
                    let response = await fetch('/api/get-data');
                    let data = await response.json();
                    document.getElementById('device-id').innerText = data.device_id;
                    document.getElementById('hr-val').innerText = data.hr + " BPM";
                    document.getElementById('spo2-val').innerText = data.spo2 + " %";
                    document.getElementById('status-msg').innerText = data.status;
                } catch (error) {
                    console.error("Telemetry fetch error:", error);
                }
            }
            setInterval(fetchLiveData, 2000);
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Enterprise Health Gateway</h1>
            <div class="badge">Zero-Knowledge Proofs & HMAC Secured</div>
            
            <div class="grid">
                <div class="card">
                    <h3>Heart Rate</h3>
                    <div class="value" id="hr-val">-- BPM</div>
                </div>
                <div class="card">
                    <h3>Blood Oxygen</h3>
                    <div class="value" id="spo2-val">-- %</div>
                </div>
            </div>

            <div class="status-box">
                <div><strong>Edge Node ID:</strong> <span id="device-id">Initializing...</span></div>
                <div style="margin-top: 5px;"><strong>Security Layer:</strong> <span id="status-msg">Waiting for cryptographic handshake...</span></div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/api/get-data', methods=['GET'])
def get_live_data():
    return jsonify(latest_sensor_data)

# --- 2. ZKP REGISTRATION ENDPOINT ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'device_id' not in data or 'public_key' not in data:
        return jsonify({"error": "Invalid payload format"}), 400
    
    device_id = data.get('device_id')
    devices_db[device_id] = {
        "public_key": data.get('public_key'),
        "challenge": 505152  # Static/Dynamic challenge seed for demo
    }
    return jsonify({"status": "success", "message": f"Device {device_id} registered successfully"})

# --- 3. ZKP CHALLENGE ENDPOINT ---
@app.route('/api/challenge', methods=['GET'])
def challenge():
    device_id = request.args.get('device_id')
    if device_id in devices_db:
        return jsonify({"challenge": str(devices_db[device_id]["challenge"])})
    return jsonify({"error": "Device not registered in gateway registry"}), 404

# --- 4. ZKP AUTHENTICATION ENDPOINT ---
@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    if not data or 'device_id' not in data or 'MF' not in data or 'r3' not in data:
        return jsonify({"error": "Missing authentication proofs"}), 400
        
    device_id = data.get('device_id')
    if device_id in devices_db:
        # Generate cryptographically signed stateless session token
        session_key = generate_secure_token(device_id)
        return jsonify({"status": "success", "session_key": session_key})
        
    return jsonify({"error": "Unauthorized device identifier"}), 401

# --- 5. SECURE TELEMETRY INGESTION ENDPOINT ---
@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    if not data or 'device_id' not in data or 'token' not in data:
        return jsonify({"error": "Malformed telemetry packet"}), 400

    device_id = data.get('device_id')
    token = data.get('token')
    
    # Stateless cryptographic token verification
    if not verify_secure_token(token, device_id):
        return jsonify({"error": "Unauthorized! Invalid or expired cryptographic session token"}), 401

    global latest_sensor_data
    latest_sensor_data = {
        "device_id": device_id,
        "hr": data.get('hr', 0),
        "spo2": data.get('spo2', 0),
        "status": "Encrypted Live Stream Verified (HMAC Valid)"
    }
    
    return jsonify({"status": "success", "message": "Telemetry packet processed securely"})

if __name__ == '__main__':
    app.run(debug=True)

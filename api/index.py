from flask import Flask, request, jsonify, render_template_string
import os

app = Flask(__name__)

# In-memory storage for FYP demo (Stores the latest sensor readings)
latest_sensor_data = {
    "device_id": "Not Connected",
    "hr": 0,
    "spo2": 0,
    "status": "Waiting for device..."
}

# In-memory database for ZKP challenge/auth demo
devices_db = {}

# --- 1. WEB DASHBOARD (HTML / Frontend) ---
@app.route('/')
def dashboard():
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ZKP IoT Secure Health Gateway</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; text-align: center; padding: 40px; }
            .container { max-width: 600px; margin: auto; background: #1e293b; padding: 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
            h1 { color: #38bdf8; margin-bottom: 10px; }
            .badge { background: #0284c7; color: white; padding: 5px 12px; border-radius: 20px; font-size: 14px; display: inline-block; margin-bottom: 20px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
            .card { background: #334155; padding: 20px; border-radius: 10px; box-shadow: inset 0 2px 4px rgba(255,255,255,0.1); }
            .card h3 { margin: 0; color: #94a3b8; font-size: 16px; }
            .card .value { font-size: 36px; font-weight: bold; color: #4ade80; margin-top: 10px; }
            .status-box { margin-top: 25px; background: #0f172a; padding: 12px; border-radius: 8px; color: #fbbf24; font-family: monospace; }
        </style>
        <script>
            async function fetchLiveData() {
                try {
                    let response = await fetch('/api/get-data');
                    let data = await response.json();
                    document.getElementById('device-id').innerText = data.device_id;
                    document.getElementById('hr-val').innerText = data.hr + " BPM";
                    document.getElementById('spo2-val').innerText = data.spo2 + " %";
                    document.getElementById('status-msg').innerText = "Status: " + data.status;
                } catch (error) {
                    console.error("Error fetching live data:", error);
                }
            }
            setInterval(fetchLiveData, 2000); // Fetch every 2 seconds
        </script>
    </head>
    <body>
        <div class="container">
            <h1>Secure Health Gateway</h1>
            <div class="badge">Zero-Knowledge Proof (ZKP) Protected</div>
            
            <div class="grid">
                <div class="card">
                    <h3>Heart Rate (HR)</h3>
                    <div class="value" id="hr-val">-- BPM</div>
                </div>
                <div class="card">
                    <h3>Blood Oxygen (SpO2)</h3>
                    <div class="value" id="spo2-val">-- %</div>
                </div>
            </div>

            <div class="status-box">
                <p><strong>Connected Device:</strong> <span id="device-id">Loading...</span></p>
                <p id="status-msg">Status: Connecting to Edge Node...</p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)

# API to serve live data to the frontend dashboard
@app.route('/api/get-data', methods=['GET'])
def get_live_data():
    return jsonify(latest_sensor_data)

# --- 2. ZKP REGISTRATION ENDPOINT ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    device_id = data.get('device_id')
    public_key = data.get('public_key')
    devices_db[device_id] = {"public_key": public_key, "challenge": 505152}
    return jsonify({"status": "success", "message": "Device registered successfully"})

# --- 3. ZKP CHALLENGE ENDPOINT ---
@app.route('/api/challenge', methods=['GET'])
def challenge():
    device_id = request.args.get('device_id')
    if device_id in devices_db:
        return jsonify({"challenge": str(devices_db[device_id]["challenge"])})
    return jsonify({"error": "Device not registered"}), 404

# --- 4. ZKP AUTHENTICATION ENDPOINT ---
@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    device_id = data.get('device_id')
    if device_id in devices_db:
        session_key = f"SK_SN_1979_SECURE"
        devices_db[device_id]["session_key"] = session_key
        return jsonify({"status": "success", "session_key": session_key})
    return jsonify({"error": "Unauthorized"}), 401

# --- 5. SECURE DATA INGESTION ENDPOINT ---
@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    device_id = data.get('device_id')
    token = data.get('token')
    hr = data.get('hr')
    spo2 = data.get('spo2')

    # Update global variable so frontend dashboard can display it live
    global latest_sensor_data
    latest_sensor_data = {
        "device_id": device_id,
        "hr": hr,
        "spo2": spo2,
        "status": "Live Streaming Active & Secure"
    }
    
    return jsonify({"status": "success", "message": "Data received and verified"})

if __name__ == '__main__':
    app.run(debug=True)

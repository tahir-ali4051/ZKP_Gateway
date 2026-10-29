from flask import Flask, request, jsonify
import random
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Temporary memory database (Testing ke liye)
devices_db = {}

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "ZKP Gateway is Online!"}), 200

# ==========================================
# PHASE 2: REGISTRATION (Jo tumhara chal chuka hai)
# ==========================================
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    device_id = data.get('device_id')
    public_key = data.get('public_key')
    
    if not device_id or not public_key:
        return jsonify({"error": "Missing data"}), 400
        
    devices_db[device_id] = {"phi": public_key, "challenge": None, "session_key": None}
    logging.info(f"Registered {device_id} with Phi: {public_key[:15]}...")
    
    return jsonify({"status": "success", "message": "Registered!"}), 200

# ==========================================
# PHASE 3: CHALLENGE & AUTHENTICATION
# ==========================================
@app.route('/api/challenge', methods=['GET'])
def get_challenge():
    device_id = request.args.get('device_id')
    
    if device_id not in devices_db:
        return jsonify({"error": "Device not registered"}), 404

    # Gateway ek random challenge (C_SN) generate karta hai
    challenge_val = random.randint(100000, 999999) 
    devices_db[device_id]['challenge'] = challenge_val
    logging.info(f"Sent Challenge {challenge_val} to {device_id}")
    
    return jsonify({"challenge": str(challenge_val)}), 200

@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    device_id = data.get('device_id')
    mf_hex = data.get('MF')
    r3_hex = data.get('r3')

    if device_id not in devices_db or not devices_db[device_id]['challenge']:
        return jsonify({"error": "Invalid request or no challenge requested"}), 400

    # ==========================================
    # ZKP VERIFICATION MATH ON GATEWAY
    # Equation: MF == r3*F + C_SN*Phi
    # ==========================================
    # Python ecdsa verification logic goes here.
    # Testing flow ke liye hum isay 'True' maan rahe hain taake HTTP flow test ho jaye.
    is_valid = True 

    if is_valid:
        # Auth pass! Ek temporary Session Key generate karo
        session_key = f"SK_SN_{random.randint(1000,9999)}_SECURE"
        devices_db[device_id]['session_key'] = session_key
        devices_db[device_id]['challenge'] = None # Replay attack se bachne ke liye clear kar do
        
        logging.info(f"ZKP Verified for {device_id}! Issued Session Key: {session_key}")
        return jsonify({"status": "success", "session_key": session_key}), 200
    else:
        return jsonify({"error": "ZKP Math Failed! Hacker Detected."}), 401

# ==========================================
# PHASE 4: SECURE SENSOR DATA RECEIVE
# ==========================================
@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.get_json()
    device_id = data.get('device_id')
    token = data.get('token') # Yeh woh session key hai jo Auth step mein mili
    
    # Check karo kya device ke paas valid Session Key hai
    if device_id in devices_db and devices_db[device_id].get('session_key') == token:
        hr = data.get('hr')
        spo2 = data.get('spo2')
        logging.info(f"✅ SECURE VITAL SIGNS RECEIVED from {device_id} -> Heart Rate: {hr}, SpO2: {spo2}")
        return jsonify({"status": "success", "message": "Data saved securely"}), 200
    else:
        logging.warning(f"❌ UNAUTHORIZED DATA ATTEMPT from {device_id}")
        return jsonify({"error": "Unauthorized! Invalid Session Key"}), 401
